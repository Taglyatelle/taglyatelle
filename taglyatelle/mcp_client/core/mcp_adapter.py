"""Adapter pattern for MCP client."""

from abc import ABC, abstractmethod
from typing import Any
from mcp import ClientSession


class GitMcpAdapter(ABC):
    """Base adapter for MCP client."""

    def __init__(self, token: str):
        raise NotImplementedError

    @abstractmethod
    async def get_available_tools(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def execute_with_context(
        self,
    ) -> tuple[list[dict[str, Any]], ClientSession | None]:
        raise NotImplementedError

    @staticmethod
    def format_tool_result(result: Any) -> str:
        raise NotImplementedError

    @staticmethod
    def build_system_prompt(
        tools: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError
