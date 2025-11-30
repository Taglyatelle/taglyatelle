"""Test webhooks."""

import pytest
from unittest.mock import Mock, MagicMock
from taglyatelle.webhooks.webhook_github import GithubWebhookAdapter


@pytest.mark.parametrize(
    "payload_bytes, secret, header, expected_detail",
    [
        (
            b'{"action": "opened"}',
            "my_secret_token",
            "",
            "x-hub-signature-256 header missing",
        ),
        (
            b'{"action": "opened"}',
            "hash_secret",
            "sha256=01532439e0104e69bb09743e6a31a0fec11216660869fb2a4891f27851723a16",
            "Signature mismatch",
        ),
        (
            b'{"action": "opened", "number": 2}',
            "hash_secret",
            "sha256=invalid_hash",
            "Signature mismatch",
        ),
    ],
)
def test_verify_signature(payload_bytes, secret, header, expected_detail):
    mock_request = Mock()
    mock_request.headers = MagicMock()

    if header:
        mock_request.headers.get.return_value = header
    else:
        mock_request.headers.get.return_value = None

    adapter = GithubWebhookAdapter(mock_request)

    try:
        adapter.verify_signature(payload_bytes, secret)
    except Exception as exc:
        assert getattr(exc, "detail", str(exc)) == expected_detail
    else:
        pytest.fail("Exception not raised for invalid signature")
