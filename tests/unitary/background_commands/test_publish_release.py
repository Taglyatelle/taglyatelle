"""Test publish_release functionality."""

import pytest
from unittest.mock import MagicMock, patch
from taglyatelle.background_commands.publish_release import (
    _bump_version,
    publish_release,
)


@pytest.fixture
def mock_provider():
    """Create a mock GitProvider instance."""
    provider = MagicMock()
    provider.get_current_tag.return_value = "1.2.3"
    provider.get_pr_body.return_value = "## Added\n- New feature"
    provider.invoke_llm.return_value = "1.3.0"
    provider.create_tag.return_value = None
    provider.create_release.return_value = None
    return provider


def test_bump_version_with_no_current_tag(mock_provider):
    """Test _bump_version when no current tag exists."""
    mock_provider.get_current_tag.return_value = None

    new_version = _bump_version(mock_provider, "Initial release")

    assert new_version == "0.1.0"
    mock_provider.get_current_tag.assert_called_once()
    mock_provider.invoke_llm.assert_not_called()


def test_bump_version_with_current_tag(mock_provider):
    """Test _bump_version when current tag exists."""
    mock_provider.get_current_tag.return_value = "1.2.3"
    mock_provider.invoke_llm.return_value = "1.3.0"
    changelog = "## Added\n- New feature"

    new_version = _bump_version(mock_provider, changelog)

    assert new_version == "1.3.0"
    mock_provider.get_current_tag.assert_called_once()
    mock_provider.invoke_llm.assert_called_once()

    # Verify the prompt contains the current version and changelog
    call_args = mock_provider.invoke_llm.call_args[0][0]
    assert "1.2.3" in call_args
    assert changelog in call_args
    assert "MAJOR" in call_args
    assert "MINOR" in call_args
    assert "PATCH" in call_args


def test_bump_version_major_change(mock_provider):
    """Test _bump_version for major breaking changes."""
    mock_provider.get_current_tag.return_value = "2.0.0"
    mock_provider.invoke_llm.return_value = "3.0.0"
    changelog = "## Breaking Changes\n- Removed deprecated API"

    new_version = _bump_version(mock_provider, changelog)

    assert new_version == "3.0.0"
    call_args = mock_provider.invoke_llm.call_args[0][0]
    assert "Breaking" in changelog or "MAJOR" in call_args


def test_bump_version_minor_change(mock_provider):
    """Test _bump_version for minor feature additions."""
    mock_provider.get_current_tag.return_value = "1.5.0"
    mock_provider.invoke_llm.return_value = "1.6.0"
    changelog = "## Added\n- New authentication method"

    new_version = _bump_version(mock_provider, changelog)

    assert new_version == "1.6.0"


def test_bump_version_patch_change(mock_provider):
    """Test _bump_version for patch/bug fixes."""
    mock_provider.get_current_tag.return_value = "1.0.4"
    mock_provider.invoke_llm.return_value = "1.0.5"
    changelog = "## Fixed\n- Bug in login flow"

    new_version = _bump_version(mock_provider, changelog)

    assert new_version == "1.0.5"


def test_bump_version_llm_returns_string_with_v_prefix(mock_provider):
    """Test _bump_version when LLM returns version with 'v' prefix."""
    mock_provider.get_current_tag.return_value = "v1.2.3"
    mock_provider.invoke_llm.return_value = "v1.3.0"

    new_version = _bump_version(mock_provider, "Changes")

    assert new_version == "v1.3.0"


def test_publish_release_success(mock_provider):
    """Test publish_release completes successfully."""
    pr_number = 42
    mock_provider.get_pr_body.return_value = "## Added\n- Feature X"
    mock_provider.invoke_llm.return_value = "2.0.0"

    with patch("taglyatelle.background_commands.publish_release.logger") as mock_logger:
        publish_release(mock_provider, pr_number)

    mock_provider.get_pr_body.assert_called_once_with(pr_number)
    mock_provider.create_tag.assert_called_once_with(tag="2.0.0")
    mock_provider.create_release.assert_called_once_with(body="## Added\n- Feature X")
    mock_logger.info.assert_called_once()
    assert "2.0.0" in mock_logger.info.call_args[0][0]
    assert f"#{pr_number}" in mock_logger.info.call_args[0][0]


def test_publish_release_with_initial_version(mock_provider):
    """Test publish_release when creating first release."""
    pr_number = 1
    mock_provider.get_current_tag.return_value = None
    mock_provider.get_pr_body.return_value = "Initial release"

    with patch("taglyatelle.background_commands.publish_release.logger"):
        publish_release(mock_provider, pr_number)

    mock_provider.create_tag.assert_called_once_with(tag="0.1.0")
    mock_provider.create_release.assert_called_once_with(body="Initial release")


def test_publish_release_with_empty_changelog(mock_provider):
    """Test publish_release with empty changelog."""
    pr_number = 10
    mock_provider.get_pr_body.return_value = ""
    mock_provider.invoke_llm.return_value = "1.0.1"

    with patch("taglyatelle.background_commands.publish_release.logger"):
        publish_release(mock_provider, pr_number)

    mock_provider.create_release.assert_called_once_with(body="")


def test_publish_release_logs_correct_info(mock_provider):
    """Test publish_release logs the correct information."""
    pr_number = 99
    mock_provider.get_pr_body.return_value = "Test changelog"
    mock_provider.invoke_llm.return_value = "3.2.1"

    with patch("taglyatelle.background_commands.publish_release.logger") as mock_logger:
        publish_release(mock_provider, pr_number)

    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Created release" in log_message
    assert "3.2.1" in log_message
    assert "PR #99" in log_message


def test_publish_release_preserves_changelog_formatting(mock_provider):
    """Test that publish_release preserves changelog markdown formatting."""
    pr_number = 15
    changelog = """## Added
- Feature A
- Feature B

## Fixed
- Bug X
- Bug Y"""

    mock_provider.get_pr_body.return_value = changelog
    mock_provider.invoke_llm.return_value = "1.1.0"

    with patch("taglyatelle.background_commands.publish_release.logger"):
        publish_release(mock_provider, pr_number)

    mock_provider.create_release.assert_called_once_with(body=changelog)


def test_bump_version_prompt_includes_semantic_versioning_guidelines(mock_provider):
    """Test that _bump_version prompt includes semantic versioning guidelines."""
    mock_provider.get_current_tag.return_value = "1.0.0"
    changelog = "Some changes"

    _bump_version(mock_provider, changelog)

    call_args = mock_provider.invoke_llm.call_args[0][0]
    assert "semantic versioning" in call_args.lower()
    assert "MAJOR" in call_args
    assert "MINOR" in call_args
    assert "PATCH" in call_args
    assert "Breaking changes" in call_args
    assert "backward-compatible" in call_args
