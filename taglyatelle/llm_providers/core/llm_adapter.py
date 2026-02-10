"""Adapter pattern for LLM providers."""

from abc import ABC, abstractmethod


class LlmAdapter(ABC):
    """Base adapter for LLM providers."""

    def __init__(self, model: str, temperature: float | int = 0):
        """
        Initialize the LLM adapter.

        Parameters
        ----------
        model
            LLM model name

        temperature
            LLM temperature
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
