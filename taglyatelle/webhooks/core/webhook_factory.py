"""Factory pattern for webhook senders."""

import ipaddress
import requests
from fastapi import HTTPException, Request, status
from taglyatelle.webhooks.core.webhook_registry import webhook_registry
from taglyatelle.webhooks.core.webhook_adapter import WebhookAdapter


class WebhookSender:
    """Adapter for multiple webhook senders."""

    def __init__(self, request: Request):
        self.request = request
        self.adapter = self._get_adapter()

    def _get_adapter(self) -> WebhookAdapter:
        """
        Get the appropriate adapter based on the provider.

        Returns
        -------
        The adapter instance
        """
        provider = self._current_git_provider()["provider"]
        adapter_cls = webhook_registry.get(provider)
        if not adapter_cls:
            raise ValueError(
                f"Unsupported provider: {provider}. Supported providers are: {list(webhook_registry.keys())}"
            )
        return adapter_cls(self.request)

    def _current_git_provider(self) -> dict[str, str]:
        """
        Get the metadata of git provider based on the request.

        Returns
        -------
        details about the git provider including its name and metadata
        """
        if "x-github-event" in self.request.headers:
            return {
                "provider": "github",
                "url": "https://api.github.com/meta",
                "key": "hooks",
            }

        raise ValueError("Unsupported git provider.")

    def allow_request(self) -> bool:
        """
        Allow request based on IP allowlist.

        Returns
        -------
        The name of the git provider if the request is allowed
        """
        details = self._current_git_provider()

        client_host = self.request.headers.get(
            "X-Forwarded-For",
            self.request.client.host,  # type: ignore
        )
        ip_only = client_host.split(":")[0]
        src_ip = ipaddress.ip_address(ip_only)

        response = requests.get(details["url"])
        response.raise_for_status()
        ip_list = response.json()[details["key"]]
        for valid_ip in ip_list:
            if src_ip in ipaddress.ip_network(valid_ip):
                return True

        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a valid ip address.")

    def verify_signature(self, payload_body: bytes, secret_token: str) -> None:
        """
        Verify the signature of the payload.

        Parameters
        ----------
        payload_body
            The raw body of the webhook payload (bytes)

        secret_token
            The webhook secret token
        """
        if self.allow_request():
            return self.adapter.verify_signature(payload_body, secret_token)
