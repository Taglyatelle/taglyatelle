"""Factory pattern for licencer providers."""

from collections.abc import Callable

from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)
from taglyatelle.slash_commands.check_licenses.core.license_registry import (
    check_license_registry,
)


class LicenseProvider:
    """Adapter for multiple license providers."""

    def __init__(self, provider: str, git_provider: "GitProvider", branch: str):
        """
        Initialize the license provider adapter.

        Parameters
        ----------
        provider
            License adapter key registered in the license registry

        git_provider
            Git provider instance used to read repository files

        branch
            Branch name to inspect
        """
        self.provider = provider
        self.git_provider = git_provider
        self.branch = branch
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> LicenseAdapter:
        """
        Get the appropriate adapter based on the provider.

        Returns
        -------
        The adapter instance
        """
        adapter_cls = check_license_registry.get(self.provider)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported provider: {self.provider}. Supported languages are: {list(check_license_registry.keys())}"
            )
        return adapter_cls()

    def _get_compliance(self, type_license: str) -> str:
        """
        Get the license compliance severity level.

        Parameters
        ----------
        type_license
            The type of license to check compliance for

        Returns
        -------
        A string report of license compliance severity
        """
        license_upper = type_license.upper()

        if any(lic in license_upper for lic in ["MIT", "APACHE", "BSD", "ISC", "PSF", "UNLIMITED"]):
            return "🟢 Low"

        if any(lic in license_upper for lic in ["LGPL", "MPL"]):
            return "🟠 Medium"

        if any(lic in license_upper for lic in ["GPL", "AGPL"]):
            return "🔴 High"

        return "⚪ Unknown"

    def parse(self) -> list[dict[str, str]] | None:
        """
        Parse the selected files to extract their licenses.

        Returns
        -------
        A list of dictionaries with package, license, and severity information,
        or None if no packages found
        """
        file_handlers = self.adapter.get_file_handlers()
        if not file_handlers:
            return None

        all_files = self.git_provider.get_repository_tree(ref=self.branch)
        if not all_files:
            return None

        available_files = []
        for file_path in all_files:
            for file_type in file_handlers.keys():
                if file_path.endswith(file_type):
                    available_files.append(file_path)
                    break

        if not available_files:
            return None

        pkg_licenses = []
        for file_path in available_files:
            file_content = self.git_provider.get_file_content(file_path=file_path, ref=self.branch)
            if not file_content:
                continue

            for file_type, handler in file_handlers.items():
                if file_path.endswith(file_type):
                    handler_func: Callable[[str], list[dict[str, str]]] = handler
                    pkg_licenses.extend(handler_func(file_content))
                    break

        if not pkg_licenses:
            return None

        for pkg_info in pkg_licenses:
            pkg_info["severity"] = self._get_compliance(pkg_info["license"])

        return pkg_licenses
