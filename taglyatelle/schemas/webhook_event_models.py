"""Pydantic models for webhook events."""

import logging
from typing import Annotated, Optional

from fastapi import Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WebhookEventModel(BaseModel):
    """Base model for webhook events."""

    event_type: str
    provider: str

    @classmethod
    def from_header(
        cls,
        x_github_event: Annotated[Optional[str], Header(alias="x-github-event")] = None,
        x_gitlab_event: Annotated[Optional[str], Header(alias="x-gitlab-event")] = None,
        x_event_key: Annotated[Optional[str], Header(alias="x-event-key")] = None,
    ) -> "WebhookEventModel":
        """
        Create WebhookEventModel from headers of different git providers.

        Parameters
        ----------
        x_github_event
            GitHub webhook event header

        x_gitlab_event
            GitLab webhook event header

        x_event_key
            Bitbucket webhook event header

        Returns
        -------
        Webhook event model with provider and event type
        """
        if x_github_event:
            logger.info(f"Received {x_github_event} event from GitHub.")
            return cls(event_type=x_github_event, provider="github")

        if x_gitlab_event:
            logger.info(f"Received {x_gitlab_event} event from GitLab.")
            event_normalized = x_gitlab_event.lower().replace(" ", "_").replace("_hook", "")
            return cls(event_type=event_normalized, provider="gitlab")

        if x_event_key:
            logger.info(f"Received {x_event_key} event from Bitbucket.")
            event_type = x_event_key.split(":")[-1] if ":" in x_event_key else x_event_key
            return cls(event_type=event_type, provider="bitbucket")

        raise ValueError("No recognized webhook event header found.")
