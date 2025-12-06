"""Check Compliance licenses"""

from datetime import datetime
import logging
from typing import Any
from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.slash_commands.check_licenses.core.license_factory import (
    LicenseProvider,
)

logging.basicConfig(level=logging.INFO)


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
    Formatted markdown table with license information
    """
    # Detect the main programming language of the repository
    main_language = provider.detect_main_language(branch=branch)

    if not main_language:
        logging.warning("Could not detect the main programming language.")
        return None

    logging.info(f"Detected main language: {main_language}")

    # Use the LicenseProvider factory to get the appropriate adapter
    try:
        license_provider = LicenseProvider(provider=main_language)
    except ValueError as e:
        logging.error(str(e))
        return None

    # Parse the licenses using the adapter
    parsed_licenses = license_provider.parse()

    if not parsed_licenses:
        logging.warning("No license information found.")
        return None

    # Format the results as a markdown table
    markdown_table = "| Package | License | Severity |\n"
    markdown_table += "|---------|---------|----------|\n"

    severity_counts = {"🟢 Low": 0, "🟠 Medium": 0, "🔴 High": 0, "⚪ Unknown": 0}

    for pkg_info in parsed_licenses:
        package_name = pkg_info.get("package", "Unknown")
        license_name = pkg_info.get("license", "Unknown")
        severity = pkg_info.get("severity", "⚪ Unknown")

        markdown_table += f"| {package_name} | {license_name} | {severity} |\n"

        # Count severity levels
        if severity in severity_counts:
            severity_counts[severity] += 1

    # Add summary
    markdown_table += "\n---\n\n**Summary:**\n"
    for severity_level, count in severity_counts.items():
        if count > 0:
            markdown_table += f"- {severity_level}: {count} package(s)\n"

    return markdown_table


def check_licenses(provider: GitProvider, payload: Any) -> None:
    """
    Check software license compliance

    Parameters
    ----------
    provider
        git provider class

    payload
        body of the request

    Notes
    -----
    Use `/check_licenses` to trigger a license compliance check on the
    current pull request branch. The bot will analyze the dependencies
    and create or update an issue with the results.
    """
    pr_number = payload["issue"]["number"]
    pr_details = provider.adapter._get_request(url=f"pulls/{pr_number}").json()  # type: ignore

    # Run the license check using the clean implementation
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
    issue_body = f"""{license_analysis}
---
<sub>*Updated: {current_date}*</sub>
"""

    if existing_issues:
        issue_number = provider.update_issue(
            issue_number=existing_issues[0]["number"],
            body=issue_body,
        )
    else:
        issue_number = provider.create_issue(
            title="Check software license compliance",
            body=issue_body,
            labels=["taglyatelle[bot]", "license-compliance"],
        )

    provider.create_pr_comment(
        pr_number=pr_number,
        message=f"✅ License compliance check completed! See issue #{issue_number} for details.",
    )

    logging.info("/check_licenses performed.")
