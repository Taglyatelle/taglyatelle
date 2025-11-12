"""Registry pattern for webhook senders."""

from typing import Type
from taglyatelle.webhooks.core.webhook_adapter import WebhookAdapter
from taglyatelle.webhooks.webhook_github import GithubWebhookAdapter
from taglyatelle.git_providers.core.git_registry import git_provider_registry


webhook_registry: dict[str, Type[WebhookAdapter]] = {}
webhook_registry.update(
    dict(zip(list(git_provider_registry.keys()), [GithubWebhookAdapter]))
)
