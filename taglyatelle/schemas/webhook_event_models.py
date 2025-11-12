"""Pydantic models for webhook events."""

from pydantic import BaseModel
from fastapi import Header
from typing import Annotated
import logging

logger = logging.getLogger(__name__)


class WebhookEventModel(BaseModel):
    """Base model for webhook events."""

    event_type: str
    provider: str

    @classmethod
    def from_header(
        cls, x_github_event: Annotated[str, Header(alias="x-github-event")]
    ) -> "WebhookEventModel":
        """Create WebhookEventModel from header."""
        logger.info(f"Received {x_github_event} event from Github.")
        return cls(event_type=x_github_event, provider="github")
