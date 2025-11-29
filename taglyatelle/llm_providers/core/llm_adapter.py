"""Adapter pattern for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any


class LlmAdapter(ABC):
    """Base adapter for LLM providers."""

    def __init__(self, model: str, temperature: float | int = 0):
        raise NotImplementedError

    @abstractmethod
    def invoke_llm(self, prompt: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def invoke_with_tools(
        self, prompt: str, tools: list[dict], system_instruction: str
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def continue_with_tool_result(
        self,
        conversation_history: list[str],
        tool_results: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_instruction: str,
    ) -> dict[str, Any]:
        raise NotImplementedError
