"""Registry pattern for LLM providers."""

from typing import Literal, Type

from taglyatelle.llm_providers.anthropic_api import AnthropicAdapter
from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter
from taglyatelle.llm_providers.gemini_api import GeminiAdapter
from taglyatelle.llm_providers.meta_api import MetaAdapter
from taglyatelle.llm_providers.mistral_api import MistralAdapter
from taglyatelle.llm_providers.openai_api import OpenAIAdapter

llm_provider_registry: dict[str, Type[LlmAdapter]] = {}


def register_llm_provider(
    name: Literal["openai", "anthropic", "gemini", "meta", "mistral"],
    adapter_cls: Type[LlmAdapter],
) -> None:
    """
    Register an LLM provider.

    Parameters
    ----------
    name
        The name of the LLM provider

    adapter_cls
        The adapter class for the LLM provider
    """
    llm_provider_registry[name] = adapter_cls


register_llm_provider("openai", OpenAIAdapter)
register_llm_provider("anthropic", AnthropicAdapter)
register_llm_provider("gemini", GeminiAdapter)
register_llm_provider("meta", MetaAdapter)
register_llm_provider("mistral", MistralAdapter)
