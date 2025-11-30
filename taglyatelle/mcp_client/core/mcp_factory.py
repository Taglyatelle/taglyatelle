"""Factory pattern for MCP client."""

from taglyatelle.mcp_client.core.mcp_adapter import GitMcpAdapter
from taglyatelle.mcp_client.core.mcp_registry import mcp_client_registry


class McpClient:
    """Adapter for multiple MCP client."""

    def __init__(self, client: str, token: str):
        self.client = client
        self.token = token
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> GitMcpAdapter:
        """
        Get the appropriate adapter based on the mcp client.

        Returns
        -------
        The adapter instance
        """
        adapter_cls = mcp_client_registry.get(self.client)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported client: {self.client}. Supported clients are: {list(mcp_client_registry.keys())}"
            )
        return adapter_cls(self.token)

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
