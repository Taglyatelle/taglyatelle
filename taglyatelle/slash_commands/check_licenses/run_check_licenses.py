"""Check Compliance licenses"""

import logging
from datetime import datetime
from itertools import islice
from typing import Any

from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.slash_commands.check_licenses.core.license_factory import (
    LicenseProvider,
)

logging.basicConfig(level=logging.INFO)

# Constants
MAX_FILES_TO_SAMPLE = 20
RELEVANT_EXTENSIONS = {
    ".py",
    ".R",
}


def _detect_main_language(provider: GitProvider, branch: str) -> str | None:
    """
    Detect the main programming language of the repository using LLM.

    Parameters
    ----------
    provider
        Git provider instance
    branch
        The branch to analyze

    Returns
    -------
    Main programming language (e.g., 'python', 'javascript', 'java')
    """
    files = provider.get_repository_tree(ref=branch)

    sample_files = list(
        islice(
            (f for f in files if any(f.endswith(ext) for ext in RELEVANT_EXTENSIONS)),
            MAX_FILES_TO_SAMPLE,
        )
    )

    language_prompt = f"""
    Analyze the following file paths from a repository and determine the main programming language.

    Files:
    {chr(10).join(sample_files)}

    Based on the file extensions and patterns, identify the PRIMARY programming language used in this repository.
    Respond with ONLY the language name in lowercase: 'python' or 'r'.
    If the main language cannot be clearly determined or is neither Python nor R, respond with 'unknown'.
    Do not include any explanation, just the language name.
    """

    response = provider.invoke_llm(language_prompt)
    if response:
        return response.strip().lower()
    return None


def _check_licenses(provider: GitProvider, branch: str) -> str | None:
    """
    Check software licenses used by the repository.

    Parameters
    ----------
    provider
        Git provider instance

    branch
        The branch to check for licenses

    Returns
    -------
    Formatted markdown table with license information, or None if unable to analyze
    """
    main_language = _detect_main_language(provider=provider, branch=branch)

    if not main_language:
        logging.warning("Could not detect the main programming language.")
        return None

    logging.info(f"Detected main language: {main_language}")

    try:
        license_provider = LicenseProvider(provider=main_language, git_provider=provider, branch=branch)
    except ValueError as e:
        logging.error(str(e))
        return None

    parsed_licenses = license_provider.parse()

    if not parsed_licenses:
        logging.warning("No license information found.")
        return None

    table_rows = [
        "| Package | License | Severity |",
        "|---------|---------|----------|",
    ]
    severity_counts = {"🟢 Low": 0, "🟠 Medium": 0, "🔴 High": 0, "⚪ Unknown": 0}

    for pkg_info in parsed_licenses:
        package_name = pkg_info.get("package", "Unknown")
        license_name = pkg_info.get("license", "Unknown")
        severity = pkg_info.get("severity", "⚪ Unknown")

        license_name = license_name.replace("|", "or")
        table_rows.append(f"| {package_name} | {license_name} | {severity} |")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    summary_lines = [
        f"- {severity_level}: {count} package(s)" for severity_level, count in severity_counts.items() if count > 0
    ]

    return "\n".join(
        [
            "\n".join(table_rows),
            "",
            "---",
            "",
            "**Summary:**",
            *summary_lines,
        ]
    )


def run_check_licenses(provider: GitProvider, payload: dict[str, Any]) -> None:
    """
    Check software license compliance

    Parameters
    ----------
    provider
        Git provider instance

    payload
        Body of the request containing issue information

    Notes
    -----
    Use `/check_licenses` to trigger a license compliance check on the
    current pull request branch. The bot will analyze the dependencies
    and create or update an issue with the results.
    """
    # Validate payload structure
    if not payload or "issue" not in payload or "number" not in payload["issue"]:
        logging.error("Invalid payload structure")
        return

    pr_number = payload["issue"]["number"]

    # Get PR details to extract branch information
    try:
        pr_details = provider.get_pr_details(pr_number=pr_number)
    except Exception as e:
        logging.error(f"Failed to get PR details: {e}")
        provider.create_pr_comment(
            pr_number=pr_number,
            message="❌ Unable to retrieve pull request details.",
        )
        return

    license_analysis = _check_licenses(provider=provider, branch=pr_details["head"]["ref"])

    if license_analysis is None:
        provider.create_pr_comment(
            pr_number=pr_number,
            message="❌ No dependency files found to analyze or language not supported.",
        )
        return None

    existing_issues = provider.search_issues(
        query="Check software license compliance",
        state="open",
        labels=["taglyatelle[bot]", "license-compliance"],
    )

    current_date = datetime.now().strftime("%d %B %Y")
    issue_body = f"{license_analysis}\n---\n<sub>*Updated: {current_date}*</sub>\n"

    issue_number = (
        provider.update_issue(
            issue_number=existing_issues[0]["number"],
            body=issue_body,
        )
        if existing_issues
        else provider.create_issue(
            title="Check software license compliance",
            body=issue_body,
            labels=["taglyatelle[bot]", "license-compliance"],
        )
    )

    provider.create_pr_comment(
        pr_number=pr_number,
        message=f"✅ License compliance check completed! See issue #{issue_number} for details.",
    )

    logging.info("/check_licenses performed.")
