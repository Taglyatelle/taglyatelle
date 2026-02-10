"""Builder pattern for llm providers."""

from taglyatelle.llm_providers.core.llm_factory import LlmProvider


class LlmProviderBuilder:
    """Builder for LlmProvider."""

    def __init__(self):
        """Initialize LlmProviderBuilder."""
        self._provider: str  # type: ignore
        self._model: str  # type: ignore

    def set_provider(self, provider: str) -> "LlmProviderBuilder":
        """
        Set the LLM provider name.

        Parameters
        ----------
        provider
            Provider key registered in the LLM registry

        Returns
        -------
        The builder instance
        """
        self._provider = provider
        return self

    def set_model(self, model: str) -> "LlmProviderBuilder":
        """
        Set the LLM model name.

        Parameters
        ----------
        model
            LLM model name

        Returns
        -------
        The builder instance
        """
        self._model = model
        return self

    def set_temperature(self, temperature: float | int = 0) -> "LlmProviderBuilder":
        """
        Set the LLM temperature.

        Parameters
        ----------
        temperature
            Sampling temperature

        Returns
        -------
        The builder instance
        """
        self._temperature = temperature
        return self

    def build(self) -> LlmProvider:
        """
        Build the configured LLM provider.

        Returns
        -------
        Configured LLM provider
        """
        return LlmProvider(self._provider, self._model, self._temperature)
