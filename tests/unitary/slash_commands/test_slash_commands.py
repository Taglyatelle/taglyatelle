import pytest
from taglyatelle.slash_commands.core.slash_registry import slash_command_registry
from taglyatelle.slash_commands.core.slash_factory import SlashCommand
from unittest.mock import patch


def test_slash_command_registry():
    assert set(slash_command_registry.keys()) == {"check_licenses"}


def test_slash_command_unsupported(mocker):
    """Test SlashCommand raises ValueError for unsupported commands."""
    mock_provider = mocker.Mock()
    payload = {"issue": {"number": 123}}

    with pytest.raises(ValueError, match="Unsupported command: invalid_command"):
        SlashCommand(command="invalid_command", provider=mock_provider, payload=payload)


@pytest.mark.parametrize(
    "command,mock_setup,expected_calls",
    [
        (
            "check_licenses",
            {
                "pr_details": {"head": {"ref": "feature-branch"}},
                "check_licenses_result": None,
            },
            {
                "pr_comment": {
                    "pr_number": 123,
                    "message": "❌ No dependency files found to analyze or language not supported.",
                }
            },
        ),
        (
            "check_licenses",
            {
                "pr_details": {"head": {"ref": "feature-branch"}},
                "check_licenses_result": "| Package | License | Severity |\n|---------|---------|----------|",
                "search_issues_result": [],
                "create_issue_result": 456,
            },
            {
                "check_licenses": {"branch": "feature-branch"},
                "search_issues": {
                    "query": "Check software license compliance",
                    "state": "open",
                    "labels": ["taglyatelle[bot]", "license-compliance"],
                },
                "create_issue": {
                    "title": "Check software license compliance",
                    "labels": ["taglyatelle[bot]", "license-compliance"],
                },
                "pr_comment": {
                    "pr_number": 123,
                    "message": "✅ License compliance check completed! See issue #456 for details.",
                },
            },
        ),
        (
            "check_licenses",
            {
                "pr_details": {"head": {"ref": "feature-branch"}},
                "check_licenses_result": "| Package | License | Severity |\n|---------|---------|----------|",
                "search_issues_result": [{"number": 789}],
                "update_issue_result": 789,
            },
            {
                "check_licenses": {"branch": "feature-branch"},
                "search_issues": {
                    "query": "Check software license compliance",
                    "state": "open",
                    "labels": ["taglyatelle[bot]", "license-compliance"],
                },
                "update_issue": {"issue_number": 789},
                "pr_comment": {
                    "pr_number": 123,
                    "message": "✅ License compliance check completed! See issue #789 for details.",
                },
            },
        ),
    ],
    ids=[
        "check_licenses_no_dependency_files",
        "check_licenses_creates_new_issue",
        "check_licenses_updates_existing_issue",
    ],
)
def test_slash_command_execution(mocker, command, mock_setup, expected_calls):
    """Test slash command execution with various scenarios."""
    mock_provider = mocker.Mock()

    # Setup mock responses
    mock_provider.get_pr_details.return_value = mock_setup.get("pr_details")
    mock_provider.search_issues.return_value = mock_setup.get(
        "search_issues_result", []
    )
    mock_provider.create_issue.return_value = mock_setup.get("create_issue_result")
    mock_provider.update_issue.return_value = mock_setup.get("update_issue_result")

    # Mock the internal _check_licenses function
    with patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._check_licenses"
    ) as mock_check_licenses:
        mock_check_licenses.return_value = mock_setup.get("check_licenses_result")

        payload = {"issue": {"number": 123}}

        # Execute command
        slash_cmd = SlashCommand(
            command=command, provider=mock_provider, payload=payload
        )
        slash_cmd.execute()

        # Verify expected calls
        if "check_licenses" in expected_calls:
            mock_check_licenses.assert_called_once_with(
                provider=mock_provider, **expected_calls["check_licenses"]
            )
        # Verify expected calls
        if "check_licenses" in expected_calls:
            mock_check_licenses.assert_called_once_with(
                provider=mock_provider, **expected_calls["check_licenses"]
            )

        if "search_issues" in expected_calls:
            mock_provider.search_issues.assert_called_once_with(
                **expected_calls["search_issues"]
            )

        if "create_issue" in expected_calls:
            mock_provider.create_issue.assert_called_once()
            call_args = mock_provider.create_issue.call_args[1]
            assert call_args["title"] == expected_calls["create_issue"]["title"]
            assert call_args["labels"] == expected_calls["create_issue"]["labels"]

        if "update_issue" in expected_calls:
            mock_provider.update_issue.assert_called_once()
            call_args = mock_provider.update_issue.call_args[1]
            assert (
                call_args["issue_number"]
                == expected_calls["update_issue"]["issue_number"]
            )

        if "pr_comment" in expected_calls:
            mock_provider.create_pr_comment.assert_called_once_with(
                **expected_calls["pr_comment"]
            )
