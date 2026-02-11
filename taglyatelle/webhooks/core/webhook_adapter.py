"""Adapter pattern for webhooks."""

from abc import ABC, abstractmethod

from fastapi import Request


class WebhookAdapter(ABC):
    """Base adapter for webhooks."""

    def __init__(self, request: Request):
        """
        Initialize the webhook adapter.

        Parameters
        ----------
        request
            Incoming FastAPI request
        """
        self.request = request

    @abstractmethod
    def verify_signature(self, payload_body: bytes, secret_token: str) -> None:
        """
        Verify the webhook signature.

        Parameters
        ----------
        payload_body
            Raw webhook payload bytes

        secret_token
            Webhook secret token
        """
        raise NotImplementedError
