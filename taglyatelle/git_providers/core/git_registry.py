"""Registry pattern for git providers."""

from typing import Literal, Type

from taglyatelle.git_providers.core.git_adapter import GitAdapter
from taglyatelle.git_providers.github_api import GithubAdapter

git_provider_registry: dict[str, Type[GitAdapter]] = {}


def register_git_provider(name: Literal["github"], adapter_cls: Type[GitAdapter]) -> None:
    """
    Register a git provider.

    Parameters
    ----------
    name
        The name of the git provider

    adapter_cls
        The adapter class for the git provider
    """
    git_provider_registry[name] = adapter_cls


register_git_provider("github", GithubAdapter)
