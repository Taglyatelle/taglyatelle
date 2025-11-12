"""Define Mistral adapter class."""

import os
from dotenv import load_dotenv
from mistralai import Mistral
from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter

if os.path.exists(".env"):
    load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class MistralAdapter(LlmAdapter):
    """Define Mistral adapter class."""

    def __init__(self, model: str, temperature: float | int = 0):
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
