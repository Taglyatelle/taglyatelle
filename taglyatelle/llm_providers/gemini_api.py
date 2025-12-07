"""Define Gemini adapter class."""

import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter

if os.path.exists(".env"):
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiAdapter(LlmAdapter):
    """Define Gemini adapter class."""

    def __init__(self, model: str, temperature: float | int = 0):
        self.client = genai.Client()
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
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
            ),
        )
        return response.text

    def _build_function_declarations(
        self, tools: list[dict[str, Any]]
    ) -> list[types.FunctionDeclaration]:
        """
        Build Gemini function declarations from MCP tools.

        Parameters
        ----------
        tools
            List of MCP tool definitions

        Returns
        -------
        List of Gemini FunctionDeclaration objects
        """
        function_declarations = []
        for tool in tools:
            sanitized_schema = self._sanitize_schema(tool.get("input_schema", {}))
            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=types.Schema(**sanitized_schema),
                )
            )
        return function_declarations

    @staticmethod
    def _sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]:
        """
        Remove unsupported fields from JSON schema for Gemini API.

        Parameters
        ----------
        schema
            JSON schema from MCP tool

        Returns
        -------
        Sanitized schema compatible with Gemini
        """
        if not isinstance(schema, dict):
            return schema

        sanitized = {}
        for key, value in schema.items():
            if key in ("additional_properties", "additionalProperties"):
                continue

            if isinstance(value, dict):
                sanitized[key] = GeminiAdapter._sanitize_schema(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    GeminiAdapter._sanitize_schema(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

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
        function_declarations = self._build_function_declarations(tools)
        tool_config = (
            types.Tool(function_declarations=function_declarations)
            if function_declarations
            else None
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                system_instruction=system_instruction,
                tools=[tool_config] if tool_config else None,
            ),
        )

        return self._extract_response_parts(response)

    def _extract_response_parts(self, response: Any) -> dict[str, Any]:
        """
        Extract text and tool calls from Gemini response.

        Parameters
        ----------
        response
            Gemini API response object

        Returns
        -------
        Dictionary containing 'text' response and 'tool_calls' if any
        """
        tool_calls = []
        text_response = ""

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                tool_calls.append(
                    {
                        "name": part.function_call.name,
                        "arguments": dict(part.function_call.args),
                    }
                )
            elif hasattr(part, "text"):
                text_response += part.text

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
        function_declarations = self._build_function_declarations(tools)
        tool_config = (
            types.Tool(function_declarations=function_declarations)
            if function_declarations
            else None
        )

        contents = []

        for msg in conversation_history:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=msg)],
                )
            )

        for tool_result in tool_results:
            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_result["name"],
                                response={"result": tool_result["result"]},
                            )
                        )
                    ],
                )
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                system_instruction=system_instruction,
                tools=[tool_config] if tool_config else None,
            ),
        )

        return self._extract_response_parts(response)
