"""Adapter pattern for check_licenses."""

from abc import ABC, abstractmethod
from pathlib import Path


EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "__pycache__",
    "dist",
    "build",
    ".pytest_cache",
    ".tox",
    "htmlcov",
}


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
                if any(excluded in file_path.parts for excluded in EXCLUDED_DIRS):
                    continue
                if file_path.is_file():
                    found_files.append(str(file_path))
        return found_files

    @abstractmethod
    def parse(self) -> None | list[dict[str, str]]:
        raise NotImplementedError
