"""Check licenses for Python packages."""

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)

import json
import re
import tomllib
import urllib.request
from importlib import metadata
from pathlib import Path

# Constants
MAX_LICENSE_TEXT_LENGTH = 200
MAX_LINES_TO_SCAN = 15
MAX_FIRST_LINE_LENGTH = 100
PYPI_TIMEOUT_SECONDS = 5

# License detection patterns
BSD_INDICATORS = ["BSD"]
BSD_3_INDICATORS = ["3-CLAUSE", "THREE-CLAUSE", "3 CLAUSE"]
BSD_2_INDICATORS = ["2-CLAUSE", "TWO-CLAUSE", "2 CLAUSE"]
MIT_INDICATORS = ["MIT LICENSE"]
GPL_INDICATORS = ["GNU GENERAL PUBLIC LICENSE"]
GPL_V3_INDICATORS = ["VERSION 3"]
GPL_V2_INDICATORS = ["VERSION 2"]

# BSD-3-Clause structural markers
BSD_3_STRUCTURAL_MARKERS = [
    "REDISTRIBUTION AND USE",
    "IN BINARY FORM",
]
BSD_3_ENDORSEMENT_MARKERS = [
    "ENDORSE OR PROMOTE",
    "WITHOUT SPECIFIC PRIOR WRITTEN PERMISSION",
]


class PythonAdapter(LicenseAdapter):
    """Adapter for checking Python package licenses."""

    def __init__(self):
        self.file_handlers = {
            "requirements.txt": self.parse_requirements_file,
            "uv.lock": self.parse_lock_files,
            "poetry.lock": self.parse_lock_files,
        }

    def _detect_bsd_license(self, lines: list[str], license_upper: str) -> str | None:
        """
        Detect BSD license variants from license text.

        Parameters
        ----------
        lines
            Lines of license text to analyze
        license_upper
            Uppercase version of full license text

        Returns
        -------
        BSD license type if detected, None otherwise
        """
        for line in lines[:MAX_LINES_TO_SCAN]:
            line_upper = line.upper()
            if any(indicator in line_upper for indicator in BSD_INDICATORS):
                if any(indicator in line_upper for indicator in BSD_3_INDICATORS):
                    return "BSD-3-Clause"

                if any(indicator in line_upper for indicator in BSD_2_INDICATORS):
                    return "BSD-2-Clause"

                return "BSD License"

        # Detect BSD-3-Clause by structural markers
        if all(marker in license_upper for marker in BSD_3_STRUCTURAL_MARKERS) and any(
            marker in license_upper for marker in BSD_3_ENDORSEMENT_MARKERS
        ):
            return "BSD-3-Clause"

        return None

    def _detect_mit_license(self, lines: list[str]) -> bool:
        """
        Detect MIT license from license text.

        Parameters
        ----------
        lines
            Lines of license text to analyze

        Returns
        -------
        True if MIT license detected, False otherwise
        """
        for line in lines[:MAX_LINES_TO_SCAN]:
            if any(indicator in line.upper() for indicator in MIT_INDICATORS):
                return True
        return False

    def _detect_gpl_license(self, license_upper: str) -> str | None:
        """
        Detect GPL license variants from license text.

        Parameters
        ----------
        license_upper
            Uppercase version of license text

        Returns
        -------
        GPL license type if detected, None otherwise
        """
        if any(indicator in license_upper for indicator in GPL_INDICATORS):
            if any(indicator in license_upper for indicator in GPL_V3_INDICATORS):
                return "GPL-3.0"

            if any(indicator in license_upper for indicator in GPL_V2_INDICATORS):
                return "GPL-2.0"

            return "GPL"

        return None

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

        # Short license texts can be returned as-is
        if len(license_text) <= MAX_LICENSE_TEXT_LENGTH:
            return license_text

        # Parse long license texts
        lines = license_text.split("\n")
        first_line = lines[0].strip()
        license_upper = license_text.upper()

        # Try to detect BSD license
        bsd_license = self._detect_bsd_license(lines, license_upper)
        if bsd_license:
            return bsd_license

        # Try to detect MIT license
        if self._detect_mit_license(lines):
            return "MIT"

        # Try to detect GPL license
        gpl_license = self._detect_gpl_license(license_upper)
        if gpl_license:
            return gpl_license

        # Fallback to first line if meaningful
        if first_line and not first_line.startswith("Copyright"):
            return first_line[:MAX_FIRST_LINE_LENGTH]

        return "Unknown"

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
            with urllib.request.urlopen(url, timeout=PYPI_TIMEOUT_SECONDS) as response:
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
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
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
            return self._get_license_from_pypi(str(pkg_name))

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

        return self._get_license_from_pypi(str(pkg_name))

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

        packages = []
        for raw_line in lines:
            stripped = raw_line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Extract package name (before any version specifier)
            pkg_name = re.split(r"[=<>!~]", stripped)[0].strip()
            if pkg_name:
                packages.append(
                    {"package": pkg_name, "license": self._get_metadata(pkg_name)}
                )

        return packages

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
        available_files = self._search_files(list(self.file_handlers.keys()))
        if not available_files:
            return None

        pkg_licenses = []
        for file_path in available_files:
            for file_type, handler in self.file_handlers.items():
                if file_path.endswith(file_type):
                    pkg_licenses.extend(handler(file_path))
                    break

        return pkg_licenses if pkg_licenses else None
