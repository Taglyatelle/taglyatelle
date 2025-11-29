"""Adapter pattern for git providers."""


class GitAdapter:
    """Base adapter for git providers."""

    def __init__(self, owner: str, repo: str):
        raise NotImplementedError

    def get_pr_files(self, pr_number: int) -> list[dict[str, str | int]]:
        raise NotImplementedError

    def get_pr_body(self, pr_number: int) -> str:
        raise NotImplementedError

    def create_pr_body(self, pr_number: int, body: str) -> None:
        raise NotImplementedError

    def create_pr_comment(self, pr_number: int, message: str) -> None:
        raise NotImplementedError

    def get_current_tag(self) -> None | str:
        raise NotImplementedError

    def create_tag(self, tag: str) -> None:
        raise NotImplementedError

    def create_release(self, body: str) -> None:
        raise NotImplementedError

    def create_issue(
        self, title: str, body: str, labels: list[str] | None = None
    ) -> int:
        raise NotImplementedError

    def search_issues(
        self, query: str, state: str = "open", labels: list[str] | None = None
    ) -> list[dict]:
        raise NotImplementedError

    def update_issue(
        self,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> int:
        raise NotImplementedError
