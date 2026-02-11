"""Adapter pattern for git providers."""


class GitAdapter:
    """Base adapter for git providers."""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the git adapter.

        Parameters
        ----------
        owner
            Repository owner or organization

        repo
            Repository name
        """
        raise NotImplementedError

    def get_pr_files(self, pr_number: int) -> list[dict[str, str | int]]:
        """
        Retrieve the files changed in a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        List of file metadata dictionaries
        """
        raise NotImplementedError

    def get_pr_body(self, pr_number: int) -> str:
        """
        Retrieve the body of a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        Pull request body text
        """
        raise NotImplementedError

    def get_pr_details(self, pr_number: int) -> dict:
        """
        Retrieve pull request details.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        Dictionary with pull request details
        """
        raise NotImplementedError

    def create_pr_body(self, pr_number: int, body: str) -> None:
        """
        Update the pull request body.

        Parameters
        ----------
        pr_number
            Pull request number

        body
            Pull request body text
        """
        raise NotImplementedError

    def create_pr_comment(self, pr_number: int, message: str) -> None:
        """
        Create a comment on a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        message
            Comment message
        """
        raise NotImplementedError

    def get_current_tag(self) -> None | str:
        """
        Get the latest tag for the repository.

        Returns
        -------
        Tag name or None if no tag exists
        """
        raise NotImplementedError

    def create_tag(self, tag: str) -> None:
        """
        Create a tag on the repository.

        Parameters
        ----------
        tag
            Tag name
        """
        raise NotImplementedError

    def create_release(self, body: str) -> None:
        """
        Create a release for the repository.

        Parameters
        ----------
        body
            Release body text
        """
        raise NotImplementedError

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> int:
        """
        Create an issue in the repository.

        Parameters
        ----------
        title
            Issue title

        body
            Issue body

        labels
            Optional list of labels

        Returns
        -------
        Issue number
        """
        raise NotImplementedError

    def search_issues(self, query: str, state: str = "open", labels: list[str] | None = None) -> list[dict]:
        """
        Search issues in the repository.

        Parameters
        ----------
        query
            Search query

        state
            Issue state filter

        labels
            Optional list of labels to filter by

        Returns
        -------
        List of issue search results
        """
        raise NotImplementedError

    def update_issue(
        self,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> int:
        """
        Update an existing issue.

        Parameters
        ----------
        issue_number
            Issue number

        title
            Updated title

        body
            Updated body

        state
            Updated issue state

        Returns
        -------
        Issue number
        """
        raise NotImplementedError

    def get_file_content(self, file_path: str, ref: str = "main") -> str | None:
        """
        Retrieve file contents from the repository.

        Parameters
        ----------
        file_path
            Path to the file in the repository

        ref
            Git reference (branch, tag, or commit SHA)

        Returns
        -------
        File contents or None if not found
        """
        raise NotImplementedError

    def get_repository_tree(self, ref: str = "main") -> list[str]:
        """
        Retrieve the repository tree.

        Parameters
        ----------
        ref
            Git reference (branch, tag, or commit SHA)

        Returns
        -------
        List of file paths in the repository
        """
        raise NotImplementedError
