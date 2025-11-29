"""Define OpenAI adapter class."""

import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter

if os.path.exists(".env"):
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class OpenAIAdapter(LlmAdapter):
    """Define OpenAI adapter class."""

    def __init__(self, model: str, temperature: float | int = 0):
        self.client = OpenAI()
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
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
        )

        return response.choices[0].message.content

    def _build_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Build OpenAI tool definitions from MCP tools.

        Parameters
        ----------
        tools
            List of MCP tool definitions

        Returns
        -------
        List of OpenAI tool definition objects
        """
        openai_tools = []
        for tool in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("input_schema", {}),
                    },
                }
            )
        return openai_tools

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
        openai_tools = self._build_tools(tools)

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            tools=openai_tools if openai_tools else None,
        )

        result = self._extract_response_parts(response)
        result["raw_response"] = response  # Include raw response for tool call tracking
        return result

    def _extract_response_parts(self, response: Any) -> dict[str, Any]:
        """
        Extract text and tool calls from OpenAI response.

        Parameters
        ----------
        response
            OpenAI API response object

        Returns
        -------
        Dictionary containing 'text' response and 'tool_calls' if any
        """
        message = response.choices[0].message
        text_response = message.content or ""
        tool_calls = []

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append(
                    {
                        "id": tool_call.id,  # Include the tool_call_id
                        "name": tool_call.function.name,
                        "arguments": eval(tool_call.function.arguments),
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
            The assistant's message containing tool_calls (required for OpenAI)

        Returns
        -------
        Answer of the LLM
        """
        openai_tools = self._build_tools(tools)

        messages = [{"role": "system", "content": system_instruction}]

        for msg in conversation_history:
            messages.append({"role": "user", "content": msg})

        # Add the assistant's message with tool calls
        if assistant_message:
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.choices[0].message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.choices[0].message.tool_calls
                    ],
                }
            )

        # Add tool results
        for tool_result in tool_results:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_result.get("id", ""),
                    "name": tool_result["name"],
                    "content": str(tool_result["result"]),
                }
            )

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            tools=openai_tools if openai_tools else None,
        )

        return self._extract_response_parts(response)
