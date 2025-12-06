"""Check Compliance licenses"""

from datetime import datetime
import logging
from typing import Any
from taglyatelle.git_providers.core.git_factory import GitProvider

logging.basicConfig(level=logging.INFO)


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

    license_analysis = provider.check_licenses(branch=pr_details["head"]["ref"])

    if license_analysis is None:
        provider.create_pr_comment(
            pr_number=pr_number,
            message="❌ No dependency files found to analyze.",
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
        message=f"✅ License compliance check! See issue #{issue_number} for details.",
    )

    logging.info("/check_licenses performed.")
