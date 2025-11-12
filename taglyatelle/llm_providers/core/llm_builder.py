"""Builder pattern for llm providers."""

from taglyatelle.llm_providers.core.llm_factory import LlmProvider


class LlmProviderBuilder:
    """Builder for LlmProvider."""

    def __init__(self):
        self._provider: str  # type: ignore
        self._model: str  # type: ignore

    def set_provider(self, provider: str) -> "LlmProviderBuilder":
        self._provider = provider
        return self

    def set_model(self, model: str) -> "LlmProviderBuilder":
        self._model = model
        return self

    def set_temperature(self, temperature: float | int = 0) -> "LlmProviderBuilder":
        self._temperature = temperature
        return self

    def build(self) -> LlmProvider:
        return LlmProvider(self._provider, self._model, self._temperature)
