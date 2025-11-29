"""Define GitHub MCP Client."""

import json
import os
from typing import Any

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if os.path.exists(".env"):
    load_dotenv()


class GithubMcpClient:
    """Define GitHub MCP Client."""

    def __init__(self, github_token: str):
        self.github_token = github_token
        if not self.github_token:
            raise ValueError(
                "GitHub token is required. Provide it or set GITHUB_TOKEN env variable."
            )

    def _get_server_params(self) -> StdioServerParameters:
        """
        Get MCP server parameters for GitHub.

        Returns
        -------
        StdioServerParameters configured for GitHub MCP server
        """
        return StdioServerParameters(
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "-e",
                "GITHUB_PERSONAL_ACCESS_TOKEN",
                "ghcr.io/github/github-mcp-server",
            ],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": self.github_token},
        )

    async def get_available_tools(self) -> list[dict[str, Any]]:
        """
        Get list of available tools from the MCP GitHub server.

        Returns
        -------
        List of tool definitions with their schemas
        """
        try:
            server_params = self._get_server_params()
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_list = await session.list_tools()

                    return [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                        for tool in tools_list.tools
                    ]
        except Exception as e:
            print(f"Error fetching tools: {e}")
            return []

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
        try:
            server_params = self._get_server_params()
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    if result and hasattr(result, "content"):
                        return result.content
        except Exception as e:
            print(f"Error calling tool '{tool_name}': {e}")
        return None

    async def execute_with_context(
        self,
    ) -> tuple[list[dict[str, Any]], ClientSession | None]:
        """
        Create a session and return available tools with context.

        Returns
        -------
        Tuple of (available_tools, session) for LLM to use
        """
        try:
            server_params = self._get_server_params()
            read, write = await stdio_client(server_params).__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()

            tools_list = await session.list_tools()
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools_list.tools
            ]

            return tools, session
        except Exception as e:
            print(f"Error initializing MCP session: {e}")
            return [], None

    @staticmethod
    def format_tool_result(result: Any) -> str:
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
        if isinstance(result, list):
            return "\n".join(
                item.text if hasattr(item, "text") else str(item) for item in result
            )
        return str(result)

    @staticmethod
    def build_system_prompt(
        tools: list[dict[str, Any]],
        github_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Build a system prompt that includes available tools.

        Parameters
        ----------
        tools
            List of available MCP tools

        github_context
            Optional GitHub context

        Returns
        -------
        System prompt with tools description
        """
        prompt = "You have access to the following GitHub tools:\n\n"

        for tool in tools:
            prompt += f"- {tool['name']}: {tool['description']}\n"
            if tool.get("input_schema"):
                prompt += (
                    f"  Parameters: {json.dumps(tool['input_schema'], indent=2)}\n"
                )

        if github_context:
            prompt += (
                f"\n\nCurrent GitHub context:\n{json.dumps(github_context, indent=2)}"
            )

        return prompt
