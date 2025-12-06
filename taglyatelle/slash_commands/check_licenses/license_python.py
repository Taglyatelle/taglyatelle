"""Check licenses for Python packages."""

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)

import re
import tomllib
from importlib import metadata
from pathlib import Path
import urllib.request
import json


class PythonAdapter(LicenseAdapter):
    """Adapter for checking Python package licenses."""

    def __init__(self):
        self.files_to_check = [
            "requirements.txt",
            "uv.lock",
            "poetry.lock",
        ]

    def _clean_license_text(self, license_text: str) -> str:
        """
        Clean and truncate verbose license text to keep only the essential license name.

        Parameters
        ----------
        license_text
            The raw license text from metadata or PyPI.

        Returns
        -------
        Cleaned license name or identifier.
        """
        if not license_text or not license_text.strip():
            return "Unknown"

        license_text = license_text.strip()

        if len(license_text) > 200:
            lines = license_text.split("\n")
            first_line = lines[0].strip()

            if "Copyright" in first_line:
                for line in lines[:10]:
                    if "BSD" in line:
                        if "3-Clause" in line or "Three-Clause" in line:
                            return "BSD-3-Clause"
                        elif "2-Clause" in line or "Two-Clause" in line:
                            return "BSD-2-Clause"
                        return "BSD License"
                    elif "MIT" in line:
                        return "MIT"

            if "GNU GENERAL PUBLIC LICENSE" in license_text:
                if "Version 3" in license_text:
                    return "GPL-3.0"
                elif "Version 2" in license_text:
                    return "GPL-2.0"
                return "GPL"

            if "NumPy" in license_text or "numpy" in first_line.lower():
                return "BSD-3-Clause (NumPy)"

            return first_line[:100] if first_line else "Unknown"

        return license_text

    def _get_license_from_pypi(self, pkg_name: str) -> str:
        """
        Fetch license information from PyPI JSON API.

        Parameters
        ----------
        pkg_name
            The name of the package to query.

        Returns
        -------
        The license of the package as a string.
        """
        try:
            url = f"https://pypi.org/pypi/{pkg_name}/json"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())

            info = data.get("info", {})
            license_info = info.get("license")
            if license_info and license_info.strip() and license_info != "UNKNOWN":
                return self._clean_license_text(license_info)

            # Use generator expression for early exit
            classifiers = info.get("classifiers", [])
            license_classifier = next(
                (c for c in classifiers if c.startswith("License ::")), None
            )
            if license_classifier:
                parts = license_classifier.split(" :: ")
                if len(parts) >= 3:
                    return self._clean_license_text(parts[-1])

            return "Unknown"
        except Exception:
            return "Unknown"

    def _get_metadata(self, pkg_name: Path) -> str:
        """
        Get the license metadata for a given package.

        Parameters
        ----------
        pkg_name
            The name of the package to query.

        Returns
        -------
        The license of the package as a string.
        """
        try:
            meta = metadata.metadata(pkg_name)
        except metadata.PackageNotFoundError:
            return self._get_license_from_pypi(pkg_name)

        license_field = meta.get("License")
        if license_field and license_field.strip() and license_field != "UNKNOWN":
            return self._clean_license_text(license_field)

        license_expr = meta.get("License-Expression")
        if license_expr and license_expr.strip():
            return self._clean_license_text(license_expr)

        classifiers = meta.get_all("Classifier") or []
        license_classifier = next(
            (c for c in classifiers if c.startswith("License ::")), None
        )
        if license_classifier:
            parts = license_classifier.split(" :: ")
            if len(parts) >= 3:
                return self._clean_license_text(parts[-1])

        return self._get_license_from_pypi(pkg_name)

    def parse_requirements_file(self, path: str) -> list[dict[str, str]]:
        """
        Parse requirements.txt file

        Parameters
        ----------
        path
            Path of the requirements.txt

        Returns
        -------
        A list of dictionaries with package and license information
        """
        with open(path, "r") as req_file:
            lines = req_file.readlines()

        return [
            {"package": pkg_name, "license": self._get_metadata(pkg_name)}
            for raw_line in lines
            if (stripped := raw_line.strip()) and not stripped.startswith("#")
            for pkg_name in [re.split(r"[=<>!~]", stripped)[0].strip()]
            if pkg_name
        ]

    def parse_lock_files(self, path: str) -> list[dict[str, str]]:
        """
        Parse uv.lock or poetry.lock file

        Parameters
        ----------
        path
            Path of the lock file

        Returns
        -------
        A list of dictionaries with package and license information
        """
        with open(path, "rb") as lock_file:
            lock_data = tomllib.load(lock_file)

        packages = lock_data.get("package", [])
        return [
            {"package": pkg_name, "license": self._get_metadata(pkg_name)}
            for p in packages
            if (pkg_name := p.get("name"))
        ]

    def parse(self) -> None | list[dict[str, str]]:
        """
        Check the licenses of Python packages in the given project path.

        Returns
        -------
        A list of dictionaries with package and license information
        """
        available_files = self._search_files(self.files_to_check)
        if not available_files:
            return None

        pkg_licenses = []

        # Create a mapping for file handlers
        file_handlers = {
            "requirements.txt": self.parse_requirements_file,
            "uv.lock": self.parse_lock_files,
            "poetry.lock": self.parse_lock_files,
        }

        # Process files efficiently
        for file_path in available_files:
            for file_type, handler in file_handlers.items():
                if file_path.endswith(file_type):
                    pkg_licenses.extend(handler(file_path))
                    break

        return pkg_licenses if pkg_licenses else None
