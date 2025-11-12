"""Unit tests for webhook factory."""

import pytest
from fastapi import HTTPException, Request
from taglyatelle.webhooks.webhook_github import GithubWebhookAdapter
from taglyatelle.webhooks.core.webhook_registry import webhook_registry
from taglyatelle.webhooks.core.webhook_factory import WebhookSender


@pytest.fixture
def mock_request(mocker):
    """Create a mock FastAPI request."""
    request = mocker.Mock(spec=Request)
    request.headers = {"x-github-event": "push"}
    request.client = mocker.Mock()
    request.client.host = "192.30.252.1"
    return request


@pytest.fixture
def webhook_sender(mock_request):
    """Create a WebhookSender instance with a mock request."""
    return WebhookSender(request=mock_request)


def test_webhook_registry():
    """Test that webhook registry contains the expected providers."""
    assert set(webhook_registry.keys()) == {"github"}
    assert webhook_registry["github"] is GithubWebhookAdapter


def test_webhook_sender_initialization(webhook_sender):
    """Test that WebhookSender initializes correctly."""
    assert webhook_sender.request is not None
    assert webhook_sender.adapter is not None
    assert isinstance(webhook_sender.adapter, GithubWebhookAdapter)


def test_webhook_sender_get_adapter(webhook_sender):
    """Test that the correct adapter is returned."""
    adapter = webhook_sender._get_adapter()
    assert isinstance(adapter, GithubWebhookAdapter)


def test_webhook_sender_get_adapter_unsupported_provider(mocker):
    """Test that ValueError is raised for unsupported provider."""
    request = mocker.Mock(spec=Request)
    request.headers = {}

    with pytest.raises(ValueError, match="Unsupported git provider"):
        WebhookSender(request=request)


def test_webhook_sender_current_git_provider(webhook_sender):
    """Test that current git provider is correctly identified."""
    provider = webhook_sender._current_git_provider()
    assert provider["provider"] == "github"
    assert provider["url"] == "https://api.github.com/meta"
    assert provider["key"] == "hooks"


def test_allow_request_valid_ip(mocker, webhook_sender):
    """Test that allow_request returns True for valid GitHub IP."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"hooks": ["192.30.252.0/22"]}
    mock_response.raise_for_status.return_value = None

    mocker.patch(
        "taglyatelle.webhooks.core.webhook_factory.requests.get",
        return_value=mock_response,
    )

    result = webhook_sender.allow_request()
    assert result is True


def test_allow_request_invalid_ip(mocker, webhook_sender):
    """Test that allow_request raises HTTPException for invalid IP."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"hooks": ["192.30.252.0/22"]}
    mock_response.raise_for_status.return_value = None

    mocker.patch(
        "taglyatelle.webhooks.core.webhook_factory.requests.get",
        return_value=mock_response,
    )

    webhook_sender.request.client.host = "1.2.3.4"

    with pytest.raises(HTTPException) as exc_info:
        webhook_sender.allow_request()

    assert exc_info.value.status_code == 403
    assert "Not a valid ip address" in str(exc_info.value.detail)


def test_allow_request_with_x_forwarded_for(mocker, mock_request):
    """Test that allow_request handles X-Forwarded-For header."""
    mock_request.headers["X-Forwarded-For"] = "192.30.252.5:8080"
    webhook_sender = WebhookSender(request=mock_request)

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"hooks": ["192.30.252.0/22"]}
    mock_response.raise_for_status.return_value = None

    mocker.patch(
        "taglyatelle.webhooks.core.webhook_factory.requests.get",
        return_value=mock_response,
    )

    result = webhook_sender.allow_request()
    assert result is True


def test_verify_signature_valid(mocker, webhook_sender):
    """Test that verify_signature succeeds with valid signature."""
    payload_body = b'{"test": "data"}'
    secret_token = "test_secret"

    mocker.patch.object(webhook_sender, "allow_request", return_value=True)
    mocker.patch.object(webhook_sender.adapter, "verify_signature", return_value=None)

    result = webhook_sender.verify_signature(
        payload_body=payload_body, secret_token=secret_token
    )

    assert result is None
    webhook_sender.adapter.verify_signature.assert_called_once_with(
        payload_body, secret_token
    )


def test_verify_signature_calls_adapter(mocker, webhook_sender):
    """Test that verify_signature delegates to the adapter."""
    payload_body = b'{"test": "data"}'
    secret_token = "my_secret"

    mocker.patch.object(webhook_sender, "allow_request", return_value=True)
    mock_verify = mocker.patch.object(webhook_sender.adapter, "verify_signature")

    webhook_sender.verify_signature(
        payload_body=payload_body, secret_token=secret_token
    )

    mock_verify.assert_called_once_with(payload_body, secret_token)


def test_verify_signature_blocked_by_allow_request(mocker, webhook_sender):
    """Test that verify_signature is not called if allow_request fails."""
    payload_body = b'{"test": "data"}'
    secret_token = "test_secret"

    mocker.patch.object(
        webhook_sender,
        "allow_request",
        side_effect=HTTPException(status_code=403, detail="Not allowed"),
    )

    with pytest.raises(HTTPException) as exc_info:
        webhook_sender.verify_signature(
            payload_body=payload_body, secret_token=secret_token
        )

    assert exc_info.value.status_code == 403
