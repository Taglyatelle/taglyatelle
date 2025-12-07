"""Define Mistral adapter class."""

import os
from typing import Any, Union

from dotenv import load_dotenv
from mistralai import Mistral
from mistralai.models import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    Function,
    Tool,
)
from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter

if os.path.exists(".env"):
    load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class MistralAdapter(LlmAdapter):
    """Define Mistral adapter class."""

    def __init__(self, model: str, temperature: float | int = 0):
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")

        self.client = Mistral(api_key=MISTRAL_API_KEY)
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
        response = self.client.chat.complete(
            model=self.model,
            temperature=self.temperature,
            messages=[  # type: ignore
                {
                    "content": prompt,
                    "role": "user",
                },
            ],
            stream=False,
        )

        return response.choices[0].message.content  # type: ignore

    def _build_tools(self, tools: list[dict[str, Any]]) -> list[Tool]:
        """
        Build Mistral tool definitions from MCP tools.

        Parameters
        ----------
        tools
            List of MCP tool definitions

        Returns
        -------
        List of Mistral tool definition objects
        """
        mistral_tools = []
        for tool in tools:
            mistral_tools.append(
                Tool(
                    type="function",
                    function=Function(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool.get("input_schema", {}),
                    ),
                )
            )
        return mistral_tools

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
        mistral_tools = self._build_tools(tools)

        messages: list[
            Union[SystemMessage, UserMessage, AssistantMessage, ToolMessage]
        ] = [
            SystemMessage(content=system_instruction),
            UserMessage(content=prompt),
        ]

        response = self.client.chat.complete(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            tools=mistral_tools if mistral_tools else None,
            stream=False,
        )

        return self._extract_response_parts(response)

    def _extract_response_parts(self, response: Any) -> dict[str, Any]:
        """
        Extract text and tool calls from Mistral response.

        Parameters
        ----------
        response
            Mistral API response object

        Returns
        -------
        Dictionary containing 'text' response and 'tool_calls' if any
        """
        message = response.choices[0].message
        text_response = message.content or ""
        tool_calls = []

        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                tool_calls.append(
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": eval(tool_call.function.arguments),
                    }
                )

        return {
            "text": text_response,
            "tool_calls": tool_calls,
            "message": message,
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
            The assistant's message containing tool calls (optional but recommended)

        Returns
        -------
        Answer of the LLM
        """
        mistral_tools = self._build_tools(tools)

        messages: list[
            Union[SystemMessage, UserMessage, AssistantMessage, ToolMessage]
        ] = [SystemMessage(content=system_instruction)]
        for msg in conversation_history:
            messages.append(UserMessage(content=msg))

        if assistant_message:
            messages.append(assistant_message)

        for tool_result in tool_results:
            messages.append(
                ToolMessage(
                    tool_call_id=tool_result.get("id", ""),
                    name=tool_result["name"],
                    content=str(tool_result["result"]),
                )
            )

        response = self.client.chat.complete(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            tools=mistral_tools if mistral_tools else None,
            stream=False,
        )

        return self._extract_response_parts(response)
