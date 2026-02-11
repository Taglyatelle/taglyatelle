"""Expose taglyatelle as an API."""

import json
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request

from taglyatelle.background_commands.publish_release import publish_release
from taglyatelle.background_commands.synchronize_changelog import synchronize_changelog
from taglyatelle.exposition.middleware import SmeeMiddleware
from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.schemas.request_model import GitProviderRequest
from taglyatelle.schemas.webhook_event_models import WebhookEventModel
from taglyatelle.slash_commands.core.slash_factory import SlashCommand

if os.path.exists(".env"):
    load_dotenv()


app = FastAPI(title="taglyatelle", version="0.3.0")
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

    git_request = GitProviderRequest.from_payload(
        payload=payload,
        provider=webhook_event.provider,
        event_type=webhook_event.event_type,
    )

    if git_request.installation_id:
        os.environ["INSTALLATION_ID"] = str(git_request.installation_id)

    provider = GitProvider(
        git_provider=git_request.provider,
        owner=git_request.repository_owner,
        repo=git_request.repository_name,
    )

    provider.set_llm_strategy(provider=str(os.getenv("LLM_PROVIDER")), model=str(os.getenv("LLM_MODEL")))

    # Call slash commands
    if git_request.event_type == "issue_comment" and git_request.action == "created":
        if git_request.comment_body and git_request.comment_body.strip().startswith("/"):
            comment_body = git_request.comment_body.strip()
            command = comment_body.split()[0][1:].lower()
            slash_command = SlashCommand(command, provider, git_request.raw_payload)
            slash_command.execute()

    # Synchronize changelog and create releases
    if git_request.event_type in ["pull_request", "merge_request"]:
        if git_request.action in ["opened", "synchronize", "reopened"]:
            if git_request.number:
                synchronize_changelog(provider=provider, pr_number=git_request.number)

        elif git_request.is_merged and git_request.base_ref == git_request.default_branch:
            if git_request.number:
                publish_release(provider=provider, pr_number=git_request.number)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("taglyatelle.exposition.taglyatelle_api:app", host="0.0.0.0", port=8000)
