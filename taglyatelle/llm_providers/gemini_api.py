"""Define Gemini adapter class."""

import os

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
