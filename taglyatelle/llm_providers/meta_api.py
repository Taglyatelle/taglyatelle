"""Define Meta adapter class."""

import os

from dotenv import load_dotenv
from llama_api_client import LlamaAPIClient

from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter

if os.path.exists(".env"):
    load_dotenv()

LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")


class MetaAdapter(LlmAdapter):
    """Define Meta adapter class."""

    def __init__(self, model: str, temperature: float | int = 0):
        self.client = LlamaAPIClient()
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
                    "content": prompt,
                },
            ],
        )

        return response.completion_message.content.text  # type: ignore
