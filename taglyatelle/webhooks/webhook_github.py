"""Webhook handler for GitHub webhook events."""

import hmac
import hashlib
from fastapi import HTTPException
from taglyatelle.webhooks.core.webhook_adapter import WebhookAdapter


class GithubWebhookAdapter(WebhookAdapter):
    """Adapter for handling GitHub webhooks."""

    def verify_signature(self, payload_body: bytes, secret_token: str) -> None:
        """
        Verify the HMAC signature of the payload.

        Parameters
        ----------
        payload_body
            The raw body of the webhook payload (bytes)

        secret_token
            The webhook secret token
        """
        signature_header = self.request.headers.get("x-hub-signature-256")
        if not signature_header:
            raise HTTPException(
                status_code=403, detail="x-hub-signature-256 header missing"
            )

        hash_object = hmac.new(
            secret_token.encode(), payload_body, digestmod=hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()
        if not hmac.compare_digest(expected_signature, signature_header):
            raise HTTPException(status_code=403, detail="Signature mismatch")
