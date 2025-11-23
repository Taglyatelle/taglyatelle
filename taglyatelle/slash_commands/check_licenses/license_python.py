"""Check licenses for Python packages."""

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenceCheckAdapter,
)


class PythonAdapter(LicenceCheckAdapter):
    """Adapter for checking Python package licenses."""

    def parse(self, files: list[str]) -> dict[str, str]:
        """
        Check the licenses of Python packages in the given project path.

        Parameters
        ----------
        project_path
            The path to the Python project

        Returns
        -------
        dict[str, str]
            A dictionary mapping package names to their licenses
        """
        licenses = {}
        return licenses
