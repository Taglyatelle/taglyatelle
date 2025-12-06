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

            # Try info.license first
            license_info = data.get("info", {}).get("license")
            if license_info and license_info.strip() and license_info != "UNKNOWN":
                return license_info

            # Try classifiers
            classifiers = data.get("info", {}).get("classifiers", [])
            for classifier in classifiers:
                if classifier.startswith("License ::"):
                    parts = classifier.split(" :: ")
                    if len(parts) >= 3:
                        return parts[-1]

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
            meta = metadata.metadata(str(pkg_name))
        except metadata.PackageNotFoundError:
            return "Unknown"

        # Try License field first
        license_field = meta.get("License")
        if license_field and license_field.strip() and license_field != "UNKNOWN":
            return license_field

        # Try License-Expression (newer standard)
        license_expr = meta.get("License-Expression")
        if license_expr and license_expr.strip():
            return license_expr

        # Extract from Classifier metadata
        classifiers = meta.get_all("Classifier") or []
        for classifier in classifiers:
            if classifier.startswith("License ::"):
                parts = classifier.split(" :: ")
                if len(parts) >= 3:
                    return parts[-1]

        # Fallback to PyPI API if local metadata doesn't have license info
        pypi_license = self._get_license_from_pypi(str(pkg_name))
        if pypi_license != "Unknown":
            return pypi_license

        return "Unknown"

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
        pkg_licenses = []
        with open(path, "r") as req_file:
            for line in req_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                pkg_name = re.split(r"[=<>!~]", line)[0].strip()
                if pkg_name:
                    license_info = self._get_metadata(Path(pkg_name))
                    pkg_licenses.append({"package": pkg_name, "license": license_info})
        return pkg_licenses

    def parse_lock_files(self, path: str) -> list[dict[str, str]]:
        """
        Parse uv.lock file

        Parameters
        ----------
        path
            Path of the uv.lock

        Returns
        -------
        A list of dictionaries with package and license information
        """
        with open(path, "rb") as lock_file:
            lock_file = tomllib.load(lock_file)
        packages = lock_file.get("package", [])
        pkg_licenses = []
        for p in packages:
            if p.get("name"):
                license_info = self._get_metadata(Path(p.get("name")))
                pkg_licenses.append({"package": p.get("name"), "license": license_info})
        return pkg_licenses

    def parse(self) -> None | list[dict[str, str]]:
        """
        Check the licenses of Python packages in the given project path.

        Returns
        -------
        A list of dictionaries with package and license information
        """
        available_files = self._search_files(self.files_to_check)
        if available_files == []:
            return None

        pkg_licenses = []
        # Check requirements.txt file
        req_file = next(
            (f for f in available_files if f.endswith("requirements.txt")), None
        )
        if req_file:
            pkg_licenses.extend(self.parse_requirements_file(req_file))

        # Check uv.lock file
        uv_lock_file = next((f for f in available_files if f.endswith("uv.lock")), None)
        if uv_lock_file:
            pkg_licenses.extend(self.parse_lock_files(uv_lock_file))

        # Check poetry.lock file
        poetry_lock_file = next(
            (f for f in available_files if f.endswith("poetry.lock")), None
        )
        if poetry_lock_file:
            pkg_licenses.extend(self.parse_lock_files(poetry_lock_file))

        return pkg_licenses
