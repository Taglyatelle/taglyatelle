"""Registry pattern for LLM providers."""

from typing import Type, Literal
from taglyatelle.slash_commands.check_licenses.core.license_adapter import (
    LicenseAdapter,
)
from taglyatelle.slash_commands.check_licenses.license_python import PythonAdapter


check_license_registry: dict[str, Type[LicenseAdapter]] = {}


def register_license_provider(
    name: Literal["python"],
    adapter_cls: Type[LicenseAdapter],
) -> None:
    """
    Register a programming language.

    Parameters
    ----------
    name
        The name of the programming language

    adapter_cls
        The adapter class for the programming language
    """
    check_license_registry[name] = adapter_cls


register_license_provider("python", PythonAdapter)
