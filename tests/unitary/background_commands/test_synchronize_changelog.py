"""Test synchronize_changelog functionality."""

import pytest
from unittest.mock import MagicMock, patch
from taglyatelle.background_commands.synchronize_changelog import (
    synchronize_changelog,
)


@pytest.fixture
def mock_provider():
    """Create a mock GitProvider instance."""
    provider = MagicMock()
    provider.get_pr_files.return_value = []
    provider.invoke_llm.return_value = "## Added\n- New feature"
    provider.create_pr_body.return_value = None
    return provider


@pytest.fixture
def sample_pr_files():
    """Create sample PR files data."""
    return [
        {
            "filename": "src/main.py",
            "status": "modified",
            "additions": 15,
            "deletions": 5,
            "patch": "@@ -10,5 +10,15 @@\n+def new_function():\n+    pass",
        },
        {
            "filename": "tests/test_main.py",
            "status": "added",
            "additions": 25,
            "deletions": 0,
            "patch": "@@ -0,0 +1,25 @@\n+def test_new_function():\n+    pass",
        },
        {
            "filename": "docs/README.md",
            "status": "modified",
            "additions": 3,
            "deletions": 1,
            "patch": "@@ -5,1 +5,3 @@\n+Updated documentation",
        },
    ]


def test_synchronize_changelog_with_empty_files(mock_provider):
    """Test synchronize_changelog when no files are changed."""
    pr_number = 42
    mock_provider.get_pr_files.return_value = []
    mock_provider.invoke_llm.return_value = "No changes"

    with patch(
        "taglyatelle.background_commands.synchronize_changelog.logger"
    ) as mock_logger:
        synchronize_changelog(mock_provider, pr_number)

    mock_provider.get_pr_files.assert_called_once_with(pr_number)
    mock_provider.invoke_llm.assert_called_once()
    mock_provider.create_pr_body.assert_called_once_with(
        pr_number=pr_number, body="No changes"
    )
    mock_logger.info.assert_called_once()


def test_synchronize_changelog_with_multiple_files(mock_provider, sample_pr_files):
    """Test synchronize_changelog with multiple files changed."""
    pr_number = 10
    mock_provider.get_pr_files.return_value = sample_pr_files
    expected_changelog = """## Added
- test_main.py with test cases

## Modified
- main.py with new function
- README.md documentation"""

    mock_provider.invoke_llm.return_value = expected_changelog

    with patch(
        "taglyatelle.background_commands.synchronize_changelog.logger"
    ) as mock_logger:
        synchronize_changelog(mock_provider, pr_number)

    mock_provider.get_pr_files.assert_called_once_with(pr_number)
    mock_provider.invoke_llm.assert_called_once()
    mock_provider.create_pr_body.assert_called_once_with(
        pr_number=pr_number, body=expected_changelog
    )

    # Verify logging
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert f"PR #{pr_number}" in log_message
    assert expected_changelog in log_message


def test_synchronize_changelog_prompt_includes_file_details(
    mock_provider, sample_pr_files
):
    """Test that the LLM prompt includes all file details."""
    pr_number = 5
    mock_provider.get_pr_files.return_value = sample_pr_files

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    # Get the prompt sent to LLM
    call_args = mock_provider.invoke_llm.call_args[0][0]

    # Check that prompt includes all file information
    assert "src/main.py" in call_args
    assert "tests/test_main.py" in call_args
    assert "docs/README.md" in call_args
    assert "modified" in call_args
    assert "added" in call_args
    assert "+15" in call_args
    assert "-5" in call_args
    assert "+25" in call_args


def test_synchronize_changelog_prompt_format(mock_provider, sample_pr_files):
    """Test that the LLM prompt follows the expected format."""
    pr_number = 1
    mock_provider.get_pr_files.return_value = sample_pr_files

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    prompt = mock_provider.invoke_llm.call_args[0][0]

    # Check prompt structure
    assert "## Added" in prompt
    assert "## Modified" in prompt
    assert "## Fixed" in prompt
    assert "Pull Request Files Changed:" in prompt
    assert "Instructions:" in prompt
    assert "bullet points" in prompt.lower()
    assert "plain text" in prompt.lower()


def test_synchronize_changelog_with_file_status_added(mock_provider):
    """Test synchronize_changelog with only added files."""
    pr_number = 20
    files = [
        {
            "filename": "new_module.py",
            "status": "added",
            "additions": 100,
            "deletions": 0,
            "patch": "@@ -0,0 +1,100 @@\n+class NewModule:\n+    pass",
        }
    ]
    mock_provider.get_pr_files.return_value = files
    mock_provider.invoke_llm.return_value = "## Added\n- New module implementation"

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    mock_provider.create_pr_body.assert_called_once()
    assert (
        mock_provider.create_pr_body.call_args[1]["body"]
        == "## Added\n- New module implementation"
    )


def test_synchronize_changelog_with_file_status_removed(mock_provider):
    """Test synchronize_changelog with removed files."""
    pr_number = 30
    files = [
        {
            "filename": "old_module.py",
            "status": "removed",
            "additions": 0,
            "deletions": 50,
            "patch": "@@ -1,50 +0,0 @@\n-class OldModule:\n-    pass",
        }
    ]
    mock_provider.get_pr_files.return_value = files
    mock_provider.invoke_llm.return_value = "## Removed\n- Deprecated old module"

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    prompt = mock_provider.invoke_llm.call_args[0][0]
    assert "removed" in prompt


def test_synchronize_changelog_with_missing_file_fields(mock_provider):
    """Test synchronize_changelog handles missing file fields gracefully."""
    pr_number = 15
    files = [
        {
            "filename": "partial.py",
            # Missing status, additions, deletions, patch
        }
    ]
    mock_provider.get_pr_files.return_value = files
    mock_provider.invoke_llm.return_value = "## Modified\n- Updated file"

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    # Should not raise an error
    mock_provider.create_pr_body.assert_called_once()

    # Verify prompt handles missing fields with defaults
    prompt = mock_provider.invoke_llm.call_args[0][0]
    assert "partial.py" in prompt
    assert "+0" in prompt  # Default additions
    assert "-0" in prompt  # Default deletions


def test_synchronize_changelog_with_large_changes(mock_provider):
    """Test synchronize_changelog with files having large number of changes."""
    pr_number = 50
    files = [
        {
            "filename": "refactored.py",
            "status": "modified",
            "additions": 500,
            "deletions": 300,
            "patch": "@@ -1,300 +1,500 @@\n# Large refactoring",
        }
    ]
    mock_provider.get_pr_files.return_value = files
    mock_provider.invoke_llm.return_value = (
        "## Modified\n- Major refactoring of core module"
    )

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    prompt = mock_provider.invoke_llm.call_args[0][0]
    assert "+500" in prompt
    assert "-300" in prompt


def test_synchronize_changelog_logs_correct_info(mock_provider):
    """Test that synchronize_changelog logs the correct information."""
    pr_number = 77
    changelog = "## Fixed\n- Critical bug"
    mock_provider.get_pr_files.return_value = [
        {
            "filename": "fix.py",
            "status": "modified",
            "additions": 2,
            "deletions": 1,
            "patch": "",
        }
    ]
    mock_provider.invoke_llm.return_value = changelog

    with patch(
        "taglyatelle.background_commands.synchronize_changelog.logger"
    ) as mock_logger:
        synchronize_changelog(mock_provider, pr_number)

    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Changelog synchronized" in log_message
    assert f"PR #{pr_number}" in log_message
    assert changelog in log_message


def test_synchronize_changelog_converts_llm_response_to_string(mock_provider):
    """Test that synchronize_changelog converts LLM response to string."""
    pr_number = 88
    mock_provider.get_pr_files.return_value = []
    # Simulate LLM returning different types
    mock_provider.invoke_llm.return_value = "String response"

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    # Should call create_pr_body with string conversion
    call_args = mock_provider.create_pr_body.call_args
    assert isinstance(call_args[1]["body"], str)
    assert call_args[1]["body"] == "String response"


def test_synchronize_changelog_with_multiple_file_types(mock_provider):
    """Test synchronize_changelog with various file types."""
    pr_number = 60
    files = [
        {
            "filename": "src/api.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "patch": "@@ api changes",
        },
        {
            "filename": "tests/test_api.py",
            "status": "added",
            "additions": 20,
            "deletions": 0,
            "patch": "@@ new tests",
        },
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 3,
            "deletions": 1,
            "patch": "@@ docs update",
        },
        {
            "filename": "requirements.txt",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
            "patch": "@@ dependency",
        },
    ]
    mock_provider.get_pr_files.return_value = files
    mock_provider.invoke_llm.return_value = (
        "## Added\n- Tests\n\n## Modified\n- API and docs"
    )

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    prompt = mock_provider.invoke_llm.call_args[0][0]

    # Verify all files are included in prompt
    for file in files:
        assert file["filename"] in prompt


def test_synchronize_changelog_prompt_instructions(mock_provider):
    """Test that the prompt includes proper instructions for the LLM."""
    pr_number = 25
    mock_provider.get_pr_files.return_value = []

    with patch("taglyatelle.background_commands.synchronize_changelog.logger"):
        synchronize_changelog(mock_provider, pr_number)

    prompt = mock_provider.invoke_llm.call_args[0][0]

    # Check instructions
    assert "Analyze the code changes" in prompt
    assert "categorize them" in prompt
    assert "user-facing changes" in prompt
    assert "without markdown code blocks" in prompt.lower()
    assert "without" in prompt and "backticks" in prompt
