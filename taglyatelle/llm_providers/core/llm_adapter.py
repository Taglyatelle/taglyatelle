"""Adapter pattern for LLM providers."""

from abc import ABC, abstractmethod


class LlmAdapter(ABC):
    """Base adapter for LLM providers."""

    def __init__(self, model: str, temperature: float | int = 0):
        raise NotImplementedError

    @abstractmethod
    def invoke_llm(self, prompt: str) -> str | None:
        raise NotImplementedError
