"""Factory pattern for slash commands."""

from typing import Any, Callable

from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.slash_commands.core.slash_registry import slash_command_registry


class SlashCommand:
    """Adapter for multiple slash commands."""

    def __init__(self, command: str, provider: GitProvider, payload: dict[str, Any]) -> None:
        """
        Initialize the slash command.

        Parameters
        ----------
        command
            The name of the slash command to execute

        provider
            The git provider instance

        payload
            The webhook payload
        """
        self.command = command
        self.provider = provider
        self.payload = payload
        self.command_func = self._get_command_func()

    def _get_command_func(self) -> Callable:
        """
        Get the appropriate command function based on the command name.

        Returns
        -------
        The command function

        Raises
        ------
        ValueError
            If the command is not registered
        """
        command_func = slash_command_registry.get(self.command)
        if not command_func:
            raise ValueError(
                f"Unsupported command: {self.command}. Supported commands are: {list(slash_command_registry.keys())}"
            )
        return command_func

    def execute(self) -> None:
        """Execute the slash command."""
        self.command_func(provider=self.provider, payload=self.payload)
