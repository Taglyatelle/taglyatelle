"""Adapter pattern for check_licenses."""

from abc import ABC, abstractmethod
from pathlib import Path


class LicenseAdapter(ABC):
    def _search_files(
        self, files_to_check: list[str], root_path: str | Path = "."
    ) -> list[str]:
        """
        Search for relevant files in the project directory.

        Parameters
        ----------
        files_to_check
            A list of file names to search for

        root_path
            The root directory to start searching from (default: current directory)

        Returns
        -------
        A list of file paths to check for licenses
        """
        found_files = []
        root = Path(root_path)
        for file_name in files_to_check:
            for file_path in root.rglob(file_name):
                if file_path.is_file():
                    found_files.append(str(file_path))
        return found_files

    def _get_complaince(self, type_license: str) -> str:
        """
        Get the license compliance.

        Parameters
        ----------
        type_license
            The type of license to check compliance for

        Returns
        -------
        A string report of license compliance
        """
        if any(lic in type_license for lic in ["MIT", "Apache", "BSD", "ISC", "PSF"]):
            return "🟢 Low"

        if any(lic in type_license for lic in ["LGPL", "MPL"]):
            return "🟠 Medium"

        if any(lic in type_license for lic in ["GPL", "AGPL"]):
            return "🔴 High"

        return "⚪ Unknown"

    @abstractmethod
    def parse(self) -> None | list[dict[str, str]]:
        raise NotImplementedError
