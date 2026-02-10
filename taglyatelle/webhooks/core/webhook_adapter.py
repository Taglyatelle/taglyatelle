"""Adapter pattern for webhooks."""

from abc import ABC, abstractmethod

from fastapi import Request


class WebhookAdapter(ABC):
    """Base adapter for webhooks."""

    def __init__(self, request: Request):
        self.request = request

    @abstractmethod
    def verify_signature(self, payload_body: bytes, secret_token: str) -> None:
        raise NotImplementedError
