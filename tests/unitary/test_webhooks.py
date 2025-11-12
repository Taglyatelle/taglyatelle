"""Test webhooks."""

import pytest
from unittest.mock import Mock, MagicMock
from taglyatelle.webhooks.webhook_github import GithubWebhookAdapter


@pytest.mark.parametrize(
    "path, secret, header, expected_detail",
    [
        (
            "data/payload.json",
            "my_secret_token",
            "",
            "x-hub-signature-256 header missing",
        ),
        (
            "data/payload.json",
            "hash_secret",
            "sha256=01532439e0104e69bb09743e6a31a0fec11216660869fb2a4891f27851723a16",
            "Signature mismatch",
        ),
        ("data/payload.json", "hash_secret", "hash_header", "Signature mismatch"),
    ],
)
def test_verify_signature(path, secret, header, expected_detail):
    with open(path, "rb") as json_file:
        payload_bytes = json_file.read()

    # Mock the request object
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
