"""Factory pattern for licencer providers."""

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)
from taglyatelle.slash_commands.check_licenses.core.license_registry import (
    check_license_registry,
)


class LicenseProvider:
    """Adapter for multiple license providers."""

    def __init__(self, provider: str):
        self.provider = provider
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
                f"Unsupported provider: {self.provider}. Supported providers are: {list(check_license_registry.keys())}"
            )
        return adapter_cls()

    def parse(self, files: list[str]) -> dict[str, str]:
        """
        Send a request to a LLM.

        Parameters
        ----------
        files
            The list of files to parse

        Returns
        -------
        A dictionary mapping file names to their licenses
        """
        return self.adapter.parse(files)
