"""Factory pattern for MCP client."""

from taglyatelle.mcp_client.core.mcp_adapter import GitMcpAdapter
from taglyatelle.mcp_client.core.mcp_registry import mcp_client_registry
from typing import Any
from mcp import ClientSession


class McpClient:
    """Adapter for multiple MCP client."""

    def __init__(self, client: str, token: str):
        self.client = client
        self.token = token
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> GitMcpAdapter:
        """
        Get the appropriate adapter based on the mcp client.

        Returns
        -------
        The adapter instance
        """
        adapter_cls = mcp_client_registry.get(self.client)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported client: {self.client}. Supported clients are: {list(mcp_client_registry.keys())}"
            )
        return adapter_cls(self.token)

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """
        Get list of available tools from the MCP GitHub server.

        Returns
        -------
        List of tool definitions with their schemas
        """
        return await self.adapter.get_available_tools()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any | None:
        """
        Call a specific MCP tool with given arguments.

        Parameters
        ----------
        tool_name
            Name of the tool to call

        arguments
            Dictionary of arguments for the tool

        Returns
        -------
        Tool result or None if call failed
        """
        return await self.adapter.call_tool(tool_name, arguments)

    async def execute_with_context(
        self,
    ) -> tuple[list[dict[str, Any]], ClientSession | None]:
        """
        Create a session and return available tools with context.

        Returns
        -------
        Tuple of (available_tools, session) for LLM to use
        """
        return await self.adapter.execute_with_context()

    def format_tool_result(self, result: Any) -> str:
        """
        Format tool result into a readable string.

        Parameters
        ----------
        result
            Tool result from MCP

        Returns
        -------
        Formatted string representation of the result
        """
        return self.adapter.format_tool_result(result)

    def build_system_prompt(
        self,
        tools: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Build a system prompt that includes available tools.

        Parameters
        ----------
        tools
            List of available MCP tools

        context
            Optional GitHub context

        Returns
        -------
        System prompt with tools description
        """
        return self.adapter.build_system_prompt(tools, context)
