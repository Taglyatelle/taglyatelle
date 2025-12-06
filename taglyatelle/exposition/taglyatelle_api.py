"""Expose taglyatelle as an API."""

import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from taglyatelle.schemas.webhook_event_models import WebhookEventModel
from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.exposition.middleware import SmeeMiddleware
from taglyatelle.slash_commands.core.slash_factory import SlashCommand
from taglyatelle.background_commands.synchronize_changelog import synchronize_changelog

if os.path.exists(".env"):
    load_dotenv()


app = FastAPI(title="taglyatelle", version="0.1.0")
app.add_middleware(SmeeMiddleware)


@app.get("/taglyatelle/ping")
def ping() -> str:
    """Ping the taglyatelle API."""
    return "pong"


@app.post("/taglyatelle/webhooks")
async def receipt_payload(
    request: Request,
    webhook_event: WebhookEventModel = Depends(WebhookEventModel.from_header),
):
    """
    Receipt webhook events from git providers and trigger some actions.

    Parameters
    ----------
    request
        The incoming request object containing the webhook payload

    webhook_event
        The webhook event model containing the event header
    """
    payload_body = await request.body()
    payload = json.loads(payload_body)

    os.environ["INSTALLATION_ID"] = str(payload["installation"]["id"])

    provider = GitProvider(
        git_provider=webhook_event.provider,
        owner=payload["repository"]["owner"]["login"],
        repo=payload["repository"]["name"],
    )

    provider.set_llm_strategy(
        provider=str(os.getenv("LLM_PROVIDER")), model=str(os.getenv("LLM_MODEL"))
    )

    # Call slash commands
    if webhook_event.event_type == "issue_comment" and payload["action"] == "created":
        comment_body = payload["comment"]["body"].strip()

        if comment_body.startswith("/"):
            command = comment_body.split()[0][1:].lower()
            slash_command = SlashCommand(command, provider, payload)
            slash_command.execute()

    # Synchronize changelog and create releases
    if webhook_event.event_type == "pull_request":
        if payload["action"] in ["opened", "synchronize", "reopened"]:
            synchronize_changelog(provider=provider, pr_number=payload["number"])

        elif (
            payload["pull_request"]["merged"]
            and payload["pull_request"]["base"]["ref"]
            == payload["repository"]["default_branch"]
        ):
            changelog = provider.get_pr_body(payload["number"])
            new_version = provider.bump_version(changelog)
            provider.create_tag(tag=new_version)
            provider.create_release(body=changelog)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("taglyatelle.exposition.taglyatelle_api:app", host="0.0.0.0", port=8000)
