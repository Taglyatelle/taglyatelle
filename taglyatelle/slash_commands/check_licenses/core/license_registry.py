"""Registry pattern for license check providers."""

from typing import Literal, Type

from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)
from taglyatelle.slash_commands.check_licenses.license_python import PythonAdapter
from taglyatelle.slash_commands.check_licenses.license_r import RAdapter


check_license_registry: dict[str, Type[LicenseAdapter]] = {}


def register_license_provider(
    name: Literal["python", "r"],
    adapter_cls: Type[LicenseAdapter],
) -> None:
    """
    Register a programming language license adapter.

    Parameters
    ----------
    name
        The name of the programming language (e.g., 'python', 'r', 'javascript')

    adapter_cls
        The adapter class for the programming language
    """
    check_license_registry[name] = adapter_cls


register_license_provider("python", PythonAdapter)
register_license_provider("r", RAdapter)
