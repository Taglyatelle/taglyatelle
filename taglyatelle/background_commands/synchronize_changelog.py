"""Synchronize PR body with changed files."""

from taglyatelle.git_providers.core.git_factory import GitProvider
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def synchronize_changelog(provider: GitProvider, pr_number: int) -> None:
    """
    Synchronize the changelog in the PR body based on the changed files.

    Parameters
    ----------
    provider
        The GitProvider instance to interact with the git provider.

    pr_number
        The pull request number to synchronize the changelog for.
    """
    pr_files = provider.get_pr_files(pr_number)

    files_summary = []
    for file_info in pr_files:
        filename = file_info.get("filename", "")
        status = file_info.get("status", "")
        additions = file_info.get("additions", 0)
        deletions = file_info.get("deletions", 0)
        patch = file_info.get("patch", "")

        files_summary.append(f"""
            File: {filename}
            Status: {status}
            Changes: +{additions} -{deletions}
            Patch:{patch}""")

    changelog_prompt = f"""
    Based on the following pull request changes, generate a changelog description in this format:

    ## Added
    [List new features, functionality, or files that were added]

    ## Modified
    [List existing features, functionality, or files that were changed/updated]

    ## Fixed
    [List bugs, issues, or problems that were resolved]

    Pull Request Files Changed:
    {"".join(files_summary)}

    Instructions:
    - Analyze the code changes and categorize them appropriately
    - Use bullet points with clear, concise descriptions
    - Focus on user-facing changes and important technical improvements
    - If a category has no changes, omit it.
    - Keep descriptions professional and informative without too much verbosity.
    - Return ONLY the changelog content in plain text without markdown code blocks or backticks.
    """

    changelog = provider.invoke_llm(changelog_prompt)
    provider.create_pr_body(pr_number=pr_number, body=str(changelog))
    logger.info(f"Changelog synchronized for PR #{pr_number}:\n{changelog}")
