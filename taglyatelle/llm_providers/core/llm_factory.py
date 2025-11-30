"""Factory pattern for LLM providers."""

from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter
from taglyatelle.llm_providers.core.llm_registry import llm_provider_registry
from typing import Any


class LlmProvider:
    """Adapter for multiple LLM providers."""

    def __init__(self, provider: str, model: str, temperature: float | int = 0):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> LlmAdapter:
        """
        Get the appropriate adapter based on the provider.

        Returns
        -------
        The adapter instance
        """
        adapter_cls = llm_provider_registry.get(self.provider)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported provider: {self.provider}. Supported providers are: {list(llm_provider_registry.keys())}"
            )
        return adapter_cls(self.model)

    def invoke_llm(self, prompt: str) -> str | None:
        """
        Send a request to a LLM.

        Parameters
        ----------
        prompt
            The prompt to send to the LLM

        Returns
        -------
        Answer of the LLM or None
        """
        return self.adapter.invoke_llm(prompt)

    def invoke_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_instruction: str,
    ) -> dict[str, Any]:
        """
        Send a request to the LLM with MCP tools available.

        Parameters
        ----------
        prompt
            The user query/prompt to send to the LLM

        tools
            List of MCP tool definitions with name, description, and input_schema

        system_instruction
            System instruction/context for the LLM

        Returns
        -------
        Answer of the LLM
        """
        return self.adapter.invoke_with_tools(prompt, tools, system_instruction)

    def continue_with_tool_result(
        self,
        conversation_history: list[str],
        tool_results: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_instruction: str,
    ) -> dict[str, Any]:
        """
        Continue conversation after tool execution.

        Parameters
        ----------
        conversation_history
            List of previous messages in the conversation

        tool_results
            List of tool execution results

        tools
            List of MCP tool definitions

        system_instruction
            System instruction/context

        Returns
        -------
        Answer of the LLM
        """
        return self.adapter.continue_with_tool_result(
            conversation_history, tool_results, tools, system_instruction
        )
