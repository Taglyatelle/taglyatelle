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

    def get_file_content(self, file_path: str, ref: str = "main") -> str | None:
        """
        Get the content of a file from the repository.

        Parameters
        ----------
        file_path
            Path to the file in the repository

        ref
            Branch, tag, or commit SHA to get the file from

        Returns
        -------
        File content as string or None if file not found
        """
        return self.adapter.get_file_content(file_path, ref)

    def synchronize_changelog(self, content: list[dict[str, str | int]]) -> str:
        """
        Create a changelog description prompt.

        Parameters
        ----------
        content
            list of modified files

        Returns
        -------
        Generated changelog description
        """
        if self._strategy is None:
            raise ValueError("LLM strategy is not defined.")

        files_summary = []
        for file_info in content:
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
        changelog_description = self.invoke_llm(changelog_prompt)
        return str(changelog_description)

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

    def check_licenses(self, branch: str) -> str | None:
        """
        Check software licenses used by the repository.

        Parameters
        ----------
        branch
            The branch to check for licenses

        Returns
        -------
        Formatted markdown table with license information
        """
        files_content = {}
        for file_path in self.files_to_check:
            content = self.get_file_content(file_path, ref=branch)
            if content:
                files_content[file_path] = content

        if not files_content:
            return None

        license_prompt = f"""
        Analyze the following files and identify all software packages/dependencies and their licenses.

        Files:
        {chr(10).join([f"{path}:{chr(10)}{content}{chr(10)}" for path, content in files_content.items()])}

        Create a detailed analysis with:
        1. List of all packages/dependencies found
        2. For each package, identify its license type (MIT, Apache 2.0, GPL, BSD, etc.)
        3. Assign a severity level:
           - 🟢 Low: Permissive licenses (MIT, Apache, BSD)
           - 🟡 Medium: Weak copyleft (LGPL, MPL)
           - 🔴 High: Strong copyleft or commercial restrictions (GPL, AGPL, proprietary)
           - ⚪ Unknown: License not found or unclear

        Format the response as a markdown table with columns: Package | License | Severity

        Important:
        - Only include actual packages/dependencies, not base images or comments
        - Be specific about license versions when possible (e.g., "GPL-3.0" not just "GPL")
        - If you cannot determine a license, mark it as "Unknown"
        - Include a brief summary at the end with counts by severity level
        """
        license_analysis = self.invoke_llm(license_prompt)
        return str(license_analysis)
