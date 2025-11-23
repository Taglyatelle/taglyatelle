"""Registry pattern for slash commands."""

from typing import Callable
from taglyatelle.slash_commands.check_licenses.run_check_licenses import check_licenses

slash_command_registry: dict[str, Callable] = {}


def register_slash_command(name: str, command_func: Callable) -> None:
    """
    Register a slash command.

    Parameters
    ----------
    name
        The name of the slash command

    command_func
        The function to execute for the slash command
    """
    slash_command_registry[name] = command_func


register_slash_command("check_licenses", check_licenses)
