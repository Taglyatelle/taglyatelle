"""Registry pattern for MCP client."""

from typing import Type
from taglyatelle.mcp_client.core.mcp_adapter import GitMcpAdapter
from taglyatelle.webhooks.webhook_github import GithubWebhookAdapter
from taglyatelle.git_providers.core.git_registry import git_provider_registry


mcp_client_registry: dict[str, Type[GitMcpAdapter]] = {}
mcp_client_registry.update(
    dict(zip(list(git_provider_registry.keys()), [GithubWebhookAdapter]))
)
