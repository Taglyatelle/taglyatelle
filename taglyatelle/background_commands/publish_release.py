"""Bump version and create release."""

from taglyatelle.git_providers.core.git_factory import GitProvider
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _bump_version(provider: GitProvider, changelog: str) -> str:
    """
    Identify the version to bump and return the new version.

    Parameters
    ----------
    provider
        The GitProvider instance to interact with the git provider.

    changelog
        The changelog description

    Returns
    -------
    New version string in the same format as current version
    """
    current_version = provider.get_current_tag()
    if current_version is None:
        return "0.1.0"

    version_prompt = f"""
    Based on the following changelog, determine the appropriate version bump type according to semantic versioning principles.

    Current version: {current_version}

    Changelog:
    {changelog}

    Version bump guidelines:
    - MAJOR: Breaking changes, incompatible API changes, or significant architectural changes
    - MINOR: New features that are backward-compatible, significant improvements, or new functionality
    - PATCH: Bug fixes, minor improvements, documentation updates, or small non-breaking changes

    Analyze the changelog and provide the new version number that should be used.

    Instructions:
    - Return ONLY the new version number in the exact same format as the current version: X.Y.Z
    - Do not include any explanations or additional text
    - Consider the severity and scope of changes in the changelog
    - If the changelog mentions bumping version files or updating version numbers, use the current version: {current_version}
    """

    new_version = provider.invoke_llm(version_prompt)
    return str(new_version)


def publish_release(provider: GitProvider, pr_number: int) -> None:
    """
    Publish a release based on the pull request changelog.

    Parameters
    ----------
    provider
        The GitProvider instance to interact with the git provider.

    pr_number
        The pull request number to create a release for.

    Notes
    -----
    Bumps the version, creates a tag, and publishes a release using the PR body as changelog.
    """

    changelog = provider.get_pr_body(pr_number)
    new_version = _bump_version(provider, changelog)
    provider.create_tag(tag=new_version)
    provider.create_release(body=changelog)
    logger.info(f"Created release {new_version} for PR #{pr_number}")
