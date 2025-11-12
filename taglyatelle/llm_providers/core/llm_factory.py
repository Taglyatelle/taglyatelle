"""Factory pattern for LLM providers."""

from taglyatelle.llm_providers.core.llm_adapter import LlmAdapter
from taglyatelle.llm_providers.core.llm_registry import llm_provider_registry


class LlmProvider:
    """Adapter for multiple LLM providers."""

    def __init__(self, provider: str, model: str, temperature: float | int = 0):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> LlmAdapter:
        """
        Get the appropriate adapter based on the provider.

        Returns
        -------
        The adapter instance
        """
        adapter_cls = llm_provider_registry.get(self.provider)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported provider: {self.provider}. Supported providers are: {list(llm_provider_registry.keys())}"
            )
        return adapter_cls(self.model)

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
        return self.adapter.invoke_llm(prompt)
