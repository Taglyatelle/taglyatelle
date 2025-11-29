"""Factory pattern for licencer providers."""

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)
from taglyatelle.slash_commands.check_licenses.core.license_registry import (
    check_license_registry,
)

import pandas as pd


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
                f"Unsupported provider: {self.provider}. Supported languages are: {list(check_license_registry.keys())}"
            )
        return adapter_cls()

    def parse(self) -> None | list[dict[str, str]]:
        """
        Parse the selected files to extract their licenses.

        Returns
        -------
        A dictionary mapping file names to their licenses
        """
        parsing_packages = self.adapter.parse()
        df_parsing = pd.DataFrame(parsing_packages)
        df_parsing["severity"] = df_parsing["license"].apply(
            lambda x: self.adapter._get_complaince(x)
        )
        return df_parsing.to_dict("records")
