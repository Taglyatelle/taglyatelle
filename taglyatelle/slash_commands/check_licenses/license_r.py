"""Check licenses for R packages."""

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)

import json
import re
import urllib.request

CRAN_TIMEOUT_SECONDS = 5
MAX_LICENSE_TEXT_LENGTH = 200


class RAdapter(LicenseAdapter):
    """Adapter for checking R package licenses."""

    def __init__(self):
        self.file_handlers = {
            "DESCRIPTION": self.parse_description_file,
            "renv.lock": self.parse_renv_lock,
        }

    def _clean_license_text(self, license_text: str) -> str:
        """
        Clean and truncate verbose license text to keep only the essential license name.

        Parameters
        ----------
        license_text
            The raw license text from DESCRIPTION or CRAN.

        Returns
        -------
        Cleaned license name or identifier.
        """
        if not license_text or not license_text.strip():
            return "Unknown"

        license_text = license_text.strip()

        # Remove "file LICENSE" or "file LICENCE" patterns (with + or | separators)
        license_text = re.sub(
            r"\s*[\+\|]\s*file\s+LICEN[CS]E.*$", "", license_text, flags=re.IGNORECASE
        )

        # If the result is just "file LICENSE" or similar, return Unknown
        if re.match(r"^\s*file\s+LICEN[CS]E.*$", license_text, flags=re.IGNORECASE):
            return "Unknown"

        license_text = license_text.strip()
        if not license_text:
            return "Unknown"

        if len(license_text) <= MAX_LICENSE_TEXT_LENGTH:
            return license_text

        lines = license_text.split("\n")
        first_line = lines[0].strip()

        if first_line and not first_line.startswith("Copyright"):
            return first_line[:MAX_LICENSE_TEXT_LENGTH]

        return "Unknown"

    def _get_license_from_cran(self, pkg_name: str) -> str:
        """
        Fetch license information from CRAN API.

        Parameters
        ----------
        pkg_name
            The name of the package to query.

        Returns
        -------
        The license of the package as a string.
        """
        try:
            url = f"https://crandb.r-pkg.org/{pkg_name}"
            with urllib.request.urlopen(url, timeout=CRAN_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode())

            license_info = data.get("License")
            if license_info and license_info.strip():
                return self._clean_license_text(license_info)

            return "Unknown"
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            return "Unknown"
        except Exception:
            return "Unknown"

    def parse_description_file(self, content: str) -> list[dict[str, str]]:
        """
        Parse DESCRIPTION file (R package metadata).

        Parameters
        ----------
        content
            Content of the DESCRIPTION file

        Returns
        -------
        A list with a single dictionary containing the package license information
        """
        try:
            package_match = re.search(r"^Package:\s*(.+)$", content, re.MULTILINE)
            package_name = (
                package_match.group(1).strip() if package_match else "Unknown"
            )

            license_match = re.search(
                r"^License:\s*(.+?)(?=\n[A-Z][a-z]+:|$)",
                content,
                re.MULTILINE | re.DOTALL,
            )

            if license_match:
                license_text = license_match.group(1).strip()
                license_text = re.sub(r"\s+", " ", license_text)
                license_info = self._clean_license_text(license_text)
            else:
                license_info = "Unknown"

            return [{"package": package_name, "license": license_info}]

        except Exception:
            return []

    def parse_renv_lock(self, content: str) -> list[dict[str, str]]:
        """
        Parse renv.lock file (R dependency lock file).

        Parameters
        ----------
        content
            Content of the renv.lock file

        Returns
        -------
        A list of dictionaries with package and license information
        """
        try:
            lock_data = json.loads(content)

            packages = lock_data.get("Packages", {})

            pkg_licenses = []
            for pkg_name, _ in packages.items():
                license_info = self._get_license_from_cran(pkg_name)
                pkg_licenses.append({"package": pkg_name, "license": license_info})

            return pkg_licenses

        except (json.JSONDecodeError, ValueError):
            return []
        except Exception:
            return []
