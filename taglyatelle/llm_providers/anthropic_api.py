"""Define Anthropic adapter class."""

import os
from typing import Any

from dotenv import load_dotenv
from anthropic import Anthropic
from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter

if os.path.exists(".env"):
    load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class AnthropicAdapter(LlmAdapter):
    """Define Anthropic adapter class."""

    def __init__(self, model: str, temperature: float | int = 0):
        self.client = Anthropic()
        self.model = model
        self.temperature = temperature

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
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        text_block = next((b for b in response.content if hasattr(b, "text")), None)
        return text_block.text if text_block else None

    def _build_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Build Anthropic tool definitions from MCP tools.

        Parameters
        ----------
        tools
            List of MCP tool definitions

        Returns
        -------
        List of Anthropic tool definition objects
        """
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool.get("input_schema", {}),
                }
            )
        return anthropic_tools

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
        Dictionary with 'text', 'tool_calls', and 'raw_response' (the raw API response)
        """
        anthropic_tools = self._build_tools(tools)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=self.temperature,
            system=system_instruction,
            messages=[{"role": "user", "content": prompt}],
            tools=anthropic_tools if anthropic_tools else None,
        )

        result = self._extract_response_parts(response)
        result["raw_response"] = response
        return result

    def _extract_response_parts(self, response: Any) -> dict[str, Any]:
        """
        Extract text and tool calls from Anthropic response.

        Parameters
        ----------
        response
            Anthropic API response object

        Returns
        -------
        Dictionary containing 'text' response and 'tool_calls' if any
        """
        text_response = ""
        tool_calls = []

        for block in response.content:
            if hasattr(block, "text"):
                text_response += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input,
                    }
                )

        return {
            "text": text_response,
            "tool_calls": tool_calls,
        }

    def continue_with_tool_result(
        self,
        conversation_history: list[str],
        tool_results: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system_instruction: str,
        assistant_message: Any = None,
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

        assistant_message
            The assistant's message containing tool_calls (required for Anthropic)

        Returns
        -------
        Answer of the LLM
        """
        anthropic_tools = self._build_tools(tools)

        messages = []

        for msg in conversation_history:
            messages.append({"role": "user", "content": msg})

        if assistant_message:
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                }
            )

        tool_result_content = []
        for tool_result in tool_results:
            tool_result_content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_result.get("id", ""),
                    "content": str(tool_result["result"]),
                }
            )

        messages.append({"role": "user", "content": tool_result_content})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=self.temperature,
            system=system_instruction,
            messages=messages,
            tools=anthropic_tools if anthropic_tools else None,
        )

        return self._extract_response_parts(response)
