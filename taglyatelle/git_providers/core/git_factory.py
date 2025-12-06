"""Factory pattern for git providers."""

from taglyatelle.llm_providers.core.llm_factory import LlmProvider
from taglyatelle.llm_providers.core.llm_builder import LlmProviderBuilder
from taglyatelle.git_providers.core.git_adapter import GitAdapter
from taglyatelle.git_providers.core.git_registry import git_provider_registry


class GitProvider:
    """Adapter for multiple git providers."""

    def __init__(
        self,
        git_provider: str,
        owner: str,
        repo: str,
    ):
        self.provider = git_provider
        self.owner = owner
        self.repo = repo
        self.adapter = self._get_adapter()

        self._builder = LlmProviderBuilder()
        self._strategy = None

    def _get_adapter(self) -> GitAdapter:
        """
        Get the appropriate adapter based on the provider.

        Returns
        -------
        The adapter instance
        """
        adapter_cls = git_provider_registry.get(self.provider)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported provider: {self.provider}. Supported providers are: {list(git_provider_registry.keys())}"
            )
        return adapter_cls(self.owner, self.repo)

    @property
    def strategy(self) -> LlmProvider | None:
        """
        Get the LLM strategy associated with this Git provider.

        Returns
        -------
        The LLM strategy instance
        """
        return self._strategy

    def set_llm_strategy(
        self, provider: str, model: str, temperature: float | int = 0
    ) -> None:
        """
        Set the LLM strategy using the builder pattern.

        Parameters
        ----------
        provider
            LLM provider name

        model
            LLM model name

        temperature
            LLM temperature
        """
        self._builder.set_provider(provider).set_model(
            model,
        ).set_temperature(temperature)

        self._strategy = self._builder.build()  # type: ignore

    def invoke_llm(self, prompt: str) -> str | None:
        """
        Send a request to a LLM.

        Parameters
        ----------
        prompt
            The prompt to send to the LLM

        Returns
        -------
        Answer of the LLM or None
        """
        if self._strategy is None:
            raise ValueError("LLM strategy is not defined.")
        return self._strategy.invoke_llm(prompt)

    def get_file_content(self, file_path: str, ref: str = "main") -> str | None:
        """
        Get the content of a file from the repository.

        Parameters
        ----------
        file_path
            Path to the file in the repository

        ref
            Git reference (branch, tag, or commit SHA)

        Returns
        -------
        Decoded file content or None if file not found
        """
        return self.adapter.get_file_content(file_path, ref)

    def get_repository_tree(self, ref: str = "main") -> list[str]:
        """
        Get the file tree of the repository.

        Parameters
        ----------
        ref
            Git reference (branch, tag, or commit SHA)

        Returns
        -------
        List of file paths in the repository
        """
        return self.adapter.get_repository_tree(ref)

    def detect_main_language(self, branch: str = "main") -> str | None:
        """
        Detect the main programming language of the repository using LLM.

        Parameters
        ----------
        branch
            The branch to analyze

        Returns
        -------
        Main programming language (e.g., 'python', 'javascript', 'java')
        """
        if self._strategy is None:
            raise ValueError("LLM strategy is not defined.")

        # Get repository file tree
        files = self.get_repository_tree(ref=branch)

        # Sample some key files for analysis
        sample_files = [
            f
            for f in files
            if any(
                f.endswith(ext)
                for ext in [
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".go",
                    ".rb",
                    ".php",
                    ".cs",
                    ".cpp",
                    ".c",
                    ".rs",
                    ".swift",
                    ".kt",
                    "package.json",
                    "requirements.txt",
                    "pom.xml",
                    "go.mod",
                    "Gemfile",
                    "composer.json",
                    "Cargo.toml",
                    "pyproject.toml",
                ]
            )
        ][:20]  # Limit to first 20 relevant files

        language_prompt = f"""
        Analyze the following file paths from a repository and determine the main programming language.

        Files:
        {chr(10).join(sample_files)}

        Based on the file extensions and patterns, identify the PRIMARY programming language used in this repository.
        Respond with ONLY the language name in lowercase (e.g., 'python', 'javascript', 'java', 'go', 'ruby').
        Do not include any explanation, just the language name.
        """

        response = self.invoke_llm(language_prompt)
        if response:
            # Clean up the response and return lowercase language name
            return response.strip().lower()
        return None

    def get_pr_files(self, pr_number: int) -> list[dict[str, str | int]]:
        """
        Get the list of files changed in a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        List of files changed in the pull request
        """
        return self.adapter.get_pr_files(pr_number)

    def get_pr_body(self, pr_number: int) -> str:
        """
        Get the body/description of a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        The PR body text or None if not present
        """
        return self.adapter.get_pr_body(pr_number)

    def create_pr_body(self, pr_number: int, body: str) -> None:
        """
        Fill in the description body of a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        body
            Pull request body text
        """
        return self.adapter.create_pr_body(pr_number, body)

    def create_pr_comment(self, pr_number: int, message: str):
        """
        Create a comment on a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        message
            Comment message
        """
        return self.adapter.create_pr_comment(pr_number, message)

    def get_current_tag(self) -> None | str:
        """
        Get the current tag of the repository.

        Returns
        -------
        Current version of the repository
        """
        return self.adapter.get_current_tag()

    def create_tag(self, tag: str) -> None:
        """
        Create a tag in the repository.

        Parameters
        ----------
        tag
            version of the repo
        """
        return self.adapter.create_tag(tag)

    def create_release(self, body: str) -> None:
        """
        Create a release in the repository.

        Parameters
        ----------
        body
            Release notes
        """
        return self.adapter.create_release(body)

    def create_issue(
        self, title: str, body: str, labels: list[str] | None = None
    ) -> int:
        """
        Create an issue in the repository.

        Parameters
        ----------
        title
            Issue title

        body
            Issue body text

        labels
            List of label names to apply to the issue

        Returns
        -------
        Created issue number
        """
        return self.adapter.create_issue(title, body, labels)

    def search_issues(
        self, query: str, state: str = "open", labels: list[str] | None = None
    ) -> list[dict]:
        """
        Search for issues in the repository.

        Parameters
        ----------
        query
            Search query string to match in issue titles

        state
            Issue state: 'open', 'closed', or 'all'

        labels
            Filter by label names

        Returns
        -------
        List of matching issues
        """
        return self.adapter.search_issues(query, state, labels)

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
            Issue number to update

        title
            New title (optional)

        body
            New body content (optional)

        state
            New state: 'open' or 'closed' (optional)

        Returns
        -------
        Created issue number
        """
        return self.adapter.update_issue(issue_number, title, body, state)

    def bump_version(self, changelog: str) -> str:
        """
        Identify the version to bump and return the new version.

        Parameters
        ----------
        changelog
            The changelog description

        Returns
        -------
        New version string in the same format as current version
        """
        current_version = self.get_current_tag()
        if current_version is None:
            return "0.1.0"

        version_prompt = f"""
        Based on the following changelog, determine the appropriate version bump type according to semantic versioning principles.

        Current version: {current_version}

        Changelog:
        {changelog}

        Version bump guidelines:
        - MAJOR: Breaking changes, incompatible API changes, or significant architectural changes
        - MINOR: New features that are backward-compatible, significant improvements, or new functionality
        - PATCH: Bug fixes, minor improvements, documentation updates, or small non-breaking changes

        Analyze the changelog and provide the new version number that should be used.

        Instructions:
        - Return ONLY the new version number in the exact same format as the current version: X.Y.Z
        - Do not include any explanations or additional text
        - Consider the severity and scope of changes in the changelog
        - If the changelog mentions bumping version files or updating version numbers, use the current version: {current_version}
        """

        new_version = self.invoke_llm(version_prompt)
        return str(new_version)
