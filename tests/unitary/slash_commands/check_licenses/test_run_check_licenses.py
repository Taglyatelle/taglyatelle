"""Unit tests for run_check_licenses functionality."""

import pytest
from unittest.mock import Mock, patch
from taglyatelle.slash_commands.check_licenses.run_check_licenses import (
    _detect_main_language,
    _check_licenses,
    run_check_licenses,
)


@pytest.fixture
def mock_git_provider():
    """Create a mock GitProvider instance."""
    provider = Mock()
    provider.get_repository_tree = Mock()
    provider.invoke_llm = Mock()
    provider.get_pr_details = Mock()
    provider.create_pr_comment = Mock()
    provider.search_issues = Mock()
    provider.create_issue = Mock()
    provider.update_issue = Mock()
    return provider


class TestDetectMainLanguage:
    """Test _detect_main_language functionality."""

    def test_detect_python_language(self, mock_git_provider):
        """Test detection of Python as main language."""
        files = [
            "src/main.py",
            "tests/test_main.py",
            "setup.py",
            "README.md",
            "requirements.txt",
        ]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = "python"

        result = _detect_main_language(mock_git_provider, "main")

        assert result == "python"
        mock_git_provider.get_repository_tree.assert_called_once_with(ref="main")
        mock_git_provider.invoke_llm.assert_called_once()

    def test_detect_r_language(self, mock_git_provider):
        """Test detection of R as main language."""
        files = [
            "R/utils.R",
            "R/analysis.R",
            "DESCRIPTION",
            "README.md",
        ]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = "r"

        result = _detect_main_language(mock_git_provider, "develop")

        assert result == "r"
        mock_git_provider.get_repository_tree.assert_called_once_with(ref="develop")

    def test_detect_unknown_language(self, mock_git_provider):
        """Test detection returns unknown for unsupported languages."""
        files = ["index.js", "package.json", "README.md"]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = "unknown"

        result = _detect_main_language(mock_git_provider, "main")

        assert result == "unknown"

    def test_detect_language_no_llm_response(self, mock_git_provider):
        """Test detection when LLM returns no response."""
        files = ["src/main.py", "tests/test_main.py"]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = None

        result = _detect_main_language(mock_git_provider, "main")

        assert result is None

    def test_detect_language_with_whitespace(self, mock_git_provider):
        """Test detection strips whitespace from LLM response."""
        files = ["main.py"]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = "  python  \n"

        result = _detect_main_language(mock_git_provider, "main")

        assert result == "python"

    def test_detect_language_samples_files(self, mock_git_provider):
        """Test that only a sample of files is sent to LLM."""
        # Create more than MAX_FILES_TO_SAMPLE (20) files
        files = [f"file{i}.py" for i in range(50)]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = "python"

        result = _detect_main_language(mock_git_provider, "main")

        assert result == "python"
        # Check that the LLM was called and a limited set of files was passed
        llm_call_args = mock_git_provider.invoke_llm.call_args[0][0]
        # Count actual file paths (not lines containing the word 'file')
        file_count = len(
            [
                line
                for line in llm_call_args.split("\n")
                if line.strip().startswith("file") and ".py" in line
            ]
        )
        assert file_count == 20

    def test_detect_language_filters_irrelevant_extensions(self, mock_git_provider):
        """Test that only relevant file extensions are considered."""
        files = [
            "main.py",
            "script.R",
            "config.json",
            "README.md",
            "style.css",
            "test.py",
        ]
        mock_git_provider.get_repository_tree.return_value = files
        mock_git_provider.invoke_llm.return_value = "python"

        _detect_main_language(mock_git_provider, "main")

        llm_call_args = mock_git_provider.invoke_llm.call_args[0][0]
        # Should only include .py and .R files
        assert "main.py" in llm_call_args
        assert "script.R" in llm_call_args
        assert "test.py" in llm_call_args
        assert "config.json" not in llm_call_args
        assert "README.md" not in llm_call_args


class TestCheckLicenses:
    """Test _check_licenses functionality."""

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses.LicenseProvider"
    )
    def test_check_licenses_success_python(
        self, mock_license_provider_class, mock_detect_lang, mock_git_provider
    ):
        """Test successful license check for Python project."""
        mock_detect_lang.return_value = "python"

        mock_license_provider = Mock()
        mock_license_provider.parse.return_value = [
            {"package": "requests", "license": "Apache-2.0", "severity": "🟢 Low"},
            {"package": "pytest", "license": "MIT", "severity": "🟢 Low"},
        ]
        mock_license_provider_class.return_value = mock_license_provider

        result = _check_licenses(mock_git_provider, "feature-branch")

        assert result is not None
        assert "| Package | License | Severity |" in result
        assert "| requests | Apache-2.0 | 🟢 Low |" in result
        assert "| pytest | MIT | 🟢 Low |" in result
        assert "**Summary:**" in result
        assert "🟢 Low: 2 package(s)" in result
        mock_detect_lang.assert_called_once_with(
            provider=mock_git_provider, branch="feature-branch"
        )
        mock_license_provider_class.assert_called_once_with(
            provider="python", git_provider=mock_git_provider, branch="feature-branch"
        )

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses.LicenseProvider"
    )
    def test_check_licenses_with_multiple_severities(
        self, mock_license_provider_class, mock_detect_lang, mock_git_provider
    ):
        """Test license check with multiple severity levels."""
        mock_detect_lang.return_value = "python"

        mock_license_provider = Mock()
        mock_license_provider.parse.return_value = [
            {"package": "pkg1", "license": "MIT", "severity": "🟢 Low"},
            {"package": "pkg2", "license": "GPL-3.0", "severity": "🔴 High"},
            {"package": "pkg3", "license": "LGPL", "severity": "🟠 Medium"},
            {"package": "pkg4", "license": "Unknown", "severity": "⚪ Unknown"},
        ]
        mock_license_provider_class.return_value = mock_license_provider

        result = _check_licenses(mock_git_provider, "main")

        assert "🟢 Low: 1 package(s)" in result
        assert "🟠 Medium: 1 package(s)" in result
        assert "🔴 High: 1 package(s)" in result
        assert "⚪ Unknown: 1 package(s)" in result

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    def test_check_licenses_language_not_detected(
        self, mock_detect_lang, mock_git_provider
    ):
        """Test when main language cannot be detected."""
        mock_detect_lang.return_value = None

        result = _check_licenses(mock_git_provider, "main")

        assert result is None

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses.LicenseProvider"
    )
    def test_check_licenses_unsupported_language(
        self, mock_license_provider_class, mock_detect_lang, mock_git_provider
    ):
        """Test with unsupported language."""
        mock_detect_lang.return_value = "javascript"
        mock_license_provider_class.side_effect = ValueError(
            "Unsupported provider: javascript"
        )

        result = _check_licenses(mock_git_provider, "main")

        assert result is None

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses.LicenseProvider"
    )
    def test_check_licenses_no_licenses_found(
        self, mock_license_provider_class, mock_detect_lang, mock_git_provider
    ):
        """Test when no license information is found."""
        mock_detect_lang.return_value = "python"

        mock_license_provider = Mock()
        mock_license_provider.parse.return_value = None
        mock_license_provider_class.return_value = mock_license_provider

        result = _check_licenses(mock_git_provider, "main")

        assert result is None

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses.LicenseProvider"
    )
    def test_check_licenses_empty_licenses(
        self, mock_license_provider_class, mock_detect_lang, mock_git_provider
    ):
        """Test when licenses list is empty."""
        mock_detect_lang.return_value = "python"

        mock_license_provider = Mock()
        mock_license_provider.parse.return_value = []
        mock_license_provider_class.return_value = mock_license_provider

        result = _check_licenses(mock_git_provider, "main")

        assert result is None

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._detect_main_language"
    )
    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses.LicenseProvider"
    )
    def test_check_licenses_pipe_character_in_license(
        self, mock_license_provider_class, mock_detect_lang, mock_git_provider
    ):
        """Test that pipe characters in licenses are replaced."""
        mock_detect_lang.return_value = "python"

        mock_license_provider = Mock()
        mock_license_provider.parse.return_value = [
            {
                "package": "dual-license",
                "license": "MIT | Apache-2.0",
                "severity": "🟢 Low",
            },
        ]
        mock_license_provider_class.return_value = mock_license_provider

        result = _check_licenses(mock_git_provider, "main")

        assert "MIT or Apache-2.0" in result
        assert "MIT | Apache-2.0" not in result


class TestRunCheckLicenses:
    """Test run_check_licenses functionality."""

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._check_licenses"
    )
    def test_run_check_licenses_creates_new_issue(
        self, mock_check_licenses, mock_git_provider
    ):
        """Test creating a new issue when no existing issue is found."""
        payload = {"issue": {"number": 123}}
        mock_git_provider.get_pr_details.return_value = {"head": {"ref": "feature-xyz"}}
        mock_check_licenses.return_value = "| Package | License | Severity |\n|---------|---------|----------|\n| pytest | MIT | 🟢 Low |"
        mock_git_provider.search_issues.return_value = []
        mock_git_provider.create_issue.return_value = 456

        run_check_licenses(mock_git_provider, payload)

        mock_git_provider.get_pr_details.assert_called_once_with(pr_number=123)
        mock_check_licenses.assert_called_once_with(
            provider=mock_git_provider, branch="feature-xyz"
        )
        mock_git_provider.search_issues.assert_called_once_with(
            query="Check software license compliance",
            state="open",
            labels=["taglyatelle[bot]", "license-compliance"],
        )
        mock_git_provider.create_issue.assert_called_once()
        call_args = mock_git_provider.create_issue.call_args[1]
        assert call_args["title"] == "Check software license compliance"
        assert call_args["labels"] == ["taglyatelle[bot]", "license-compliance"]
        assert "pytest" in call_args["body"]
        mock_git_provider.create_pr_comment.assert_called_once_with(
            pr_number=123,
            message="✅ License compliance check completed! See issue #456 for details.",
        )

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._check_licenses"
    )
    def test_run_check_licenses_updates_existing_issue(
        self, mock_check_licenses, mock_git_provider
    ):
        """Test updating an existing issue when one is found."""
        payload = {"issue": {"number": 123}}
        mock_git_provider.get_pr_details.return_value = {"head": {"ref": "main"}}
        mock_check_licenses.return_value = "| Package | License | Severity |\n|---------|---------|----------|\n| requests | Apache-2.0 | 🟢 Low |"
        mock_git_provider.search_issues.return_value = [{"number": 789}]
        mock_git_provider.update_issue.return_value = 789

        run_check_licenses(mock_git_provider, payload)

        mock_git_provider.update_issue.assert_called_once()
        call_args = mock_git_provider.update_issue.call_args[1]
        assert call_args["issue_number"] == 789
        assert "requests" in call_args["body"]
        mock_git_provider.create_issue.assert_not_called()
        mock_git_provider.create_pr_comment.assert_called_once_with(
            pr_number=123,
            message="✅ License compliance check completed! See issue #789 for details.",
        )

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._check_licenses"
    )
    def test_run_check_licenses_no_dependency_files(
        self, mock_check_licenses, mock_git_provider
    ):
        """Test when no dependency files are found."""
        payload = {"issue": {"number": 123}}
        mock_git_provider.get_pr_details.return_value = {"head": {"ref": "main"}}
        mock_check_licenses.return_value = None

        run_check_licenses(mock_git_provider, payload)

        mock_git_provider.create_pr_comment.assert_called_once_with(
            pr_number=123,
            message="❌ No dependency files found to analyze or language not supported.",
        )
        mock_git_provider.search_issues.assert_not_called()
        mock_git_provider.create_issue.assert_not_called()
        mock_git_provider.update_issue.assert_not_called()

    def test_run_check_licenses_invalid_payload_empty(self, mock_git_provider):
        """Test with empty payload."""
        run_check_licenses(mock_git_provider, {})

        mock_git_provider.get_pr_details.assert_not_called()
        mock_git_provider.create_pr_comment.assert_not_called()

    def test_run_check_licenses_invalid_payload_no_issue(self, mock_git_provider):
        """Test with payload missing issue field."""
        run_check_licenses(mock_git_provider, {"other": "data"})

        mock_git_provider.get_pr_details.assert_not_called()
        mock_git_provider.create_pr_comment.assert_not_called()

    def test_run_check_licenses_invalid_payload_no_number(self, mock_git_provider):
        """Test with payload missing issue number."""
        run_check_licenses(mock_git_provider, {"issue": {"title": "test"}})

        mock_git_provider.get_pr_details.assert_not_called()
        mock_git_provider.create_pr_comment.assert_not_called()

    def test_run_check_licenses_pr_details_error(self, mock_git_provider):
        """Test when PR details retrieval fails."""
        payload = {"issue": {"number": 123}}
        mock_git_provider.get_pr_details.side_effect = Exception("API Error")

        run_check_licenses(mock_git_provider, payload)

        mock_git_provider.create_pr_comment.assert_called_once_with(
            pr_number=123,
            message="❌ Unable to retrieve pull request details.",
        )

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._check_licenses"
    )
    @patch("taglyatelle.slash_commands.check_licenses.run_check_licenses.datetime")
    def test_run_check_licenses_includes_timestamp(
        self, mock_datetime, mock_check_licenses, mock_git_provider
    ):
        """Test that issue body includes timestamp."""
        payload = {"issue": {"number": 123}}
        mock_git_provider.get_pr_details.return_value = {"head": {"ref": "main"}}
        mock_check_licenses.return_value = "| Package | License | Severity |"
        mock_git_provider.search_issues.return_value = []
        mock_git_provider.create_issue.return_value = 456

        # Mock datetime to return a specific date
        mock_now = Mock()
        mock_now.strftime.return_value = "15 November 2023"
        mock_datetime.now.return_value = mock_now

        run_check_licenses(mock_git_provider, payload)

        call_args = mock_git_provider.create_issue.call_args[1]
        assert "*Updated: 15 November 2023*" in call_args["body"]

    @patch(
        "taglyatelle.slash_commands.check_licenses.run_check_licenses._check_licenses"
    )
    def test_run_check_licenses_complete_flow(
        self, mock_check_licenses, mock_git_provider
    ):
        """Test complete flow with all components."""
        payload = {"issue": {"number": 100}}
        mock_git_provider.get_pr_details.return_value = {
            "head": {"ref": "develop"},
            "base": {"ref": "main"},
        }

        license_table = """| Package | License | Severity |
|---------|---------|----------|
| requests | Apache-2.0 | 🟢 Low |
| flask | BSD-3-Clause | 🟢 Low |
| django | BSD | 🟢 Low |"""

        mock_check_licenses.return_value = license_table
        mock_git_provider.search_issues.return_value = []
        mock_git_provider.create_issue.return_value = 200

        run_check_licenses(mock_git_provider, payload)

        # Verify all steps were executed
        assert mock_git_provider.get_pr_details.called
        assert mock_check_licenses.called
        assert mock_git_provider.search_issues.called
        assert mock_git_provider.create_issue.called
        assert mock_git_provider.create_pr_comment.called

        # Verify issue body contains the table
        call_args = mock_git_provider.create_issue.call_args[1]
        assert "requests" in call_args["body"]
        assert "flask" in call_args["body"]
        assert "django" in call_args["body"]
