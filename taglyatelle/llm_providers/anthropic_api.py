"""Define Anthropic adapter class."""

import os
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
