"""Integration test for taglyatelle API."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from taglyatelle.exposition.taglyatelle_api import app


@pytest.fixture
def client():
    with patch(
        "taglyatelle.exposition.taglyatelle_api.SmeeMiddleware.dispatch"
    ) as mock_dispatch:

        async def passthrough_dispatch(request, call_next):
            """Pass through without signature verification."""
            return await call_next(request)

        mock_dispatch.side_effect = passthrough_dispatch
        yield TestClient(app)


@pytest.fixture
def mock_github_payload_opened():
    """Mock GitHub webhook payload for PR opened event."""
    return {
        "action": "opened",
        "number": 123,
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
        "pull_request": {
            "number": 123,
            "merged": False,
            "base": {"ref": "main"},
        },
    }


@pytest.fixture
def mock_github_payload_merged():
    """Mock GitHub webhook payload for PR merged event."""
    return {
        "action": "closed",
        "number": 456,
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
        "pull_request": {
            "number": 456,
            "merged": True,
            "base": {"ref": "main"},
        },
    }


@pytest.fixture
def mock_pr_files():
    """Mock PR files returned by get_pr_files."""
    return [
        {
            "filename": "test.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "patch": "diff --git a/test.py b/test.py...",
        }
    ]


def test_ping_returns_pong(client):
    """Test the ping endpoint returns pong."""
    response = client.get("/taglyatelle/ping")
    assert response.status_code == 200
    assert response.json() == "pong"


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_opened(
    mock_getenv,
    mock_git_provider_class,
    client,
    mock_github_payload_opened,
    mock_pr_files,
):
    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_pr_files.return_value = mock_pr_files
    mock_provider_instance.synchronize_changelog.return_value = (
        "## Added\n- New feature"
    )
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=mock_github_payload_opened,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_git_provider_class.assert_called_once_with(
        git_provider="github",
        owner="test-owner",
        repo="test-repo",
    )
    mock_provider_instance.set_llm_strategy.assert_called_once_with(
        provider="openai", model="gpt-4"
    )
    mock_provider_instance.get_pr_files.assert_called_once_with(123)
    mock_provider_instance.synchronize_changelog.assert_called_once_with(
        content=mock_pr_files
    )
    mock_provider_instance.create_pr_body.assert_called_once_with(
        pr_number=123, body="## Added\n- New feature"
    )


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_synchronize(
    mock_getenv,
    mock_git_provider_class,
    client,
    mock_github_payload_opened,
    mock_pr_files,
):
    payload = mock_github_payload_opened.copy()
    payload["action"] = "synchronize"

    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "anthropic",
        "LLM_MODEL": "claude-3",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_pr_files.return_value = mock_pr_files
    mock_provider_instance.synchronize_changelog.return_value = (
        "## Modified\n- Updated tests"
    )
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=payload,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_provider_instance.get_pr_files.assert_called_once_with(123)
    mock_provider_instance.synchronize_changelog.assert_called_once()
    mock_provider_instance.create_pr_body.assert_called_once()


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_reopened(
    mock_getenv,
    mock_git_provider_class,
    client,
    mock_github_payload_opened,
    mock_pr_files,
):
    payload = mock_github_payload_opened.copy()
    payload["action"] = "reopened"

    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_pr_files.return_value = mock_pr_files
    mock_provider_instance.synchronize_changelog.return_value = "## Fixed\n- Bug fix"
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=payload,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_provider_instance.get_pr_files.assert_called_once_with(123)
    mock_provider_instance.create_pr_body.assert_called_once()


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_merged_to_main(
    mock_getenv, mock_git_provider_class, client, mock_github_payload_merged
):
    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_pr_body.return_value = (
        "## Added\n- New feature\n## Fixed\n- Bug fix"
    )
    mock_provider_instance.bump_version.return_value = "1.2.0"
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=mock_github_payload_merged,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_provider_instance.get_pr_body.assert_called_once_with(456)
    mock_provider_instance.bump_version.assert_called_once_with(
        "## Added\n- New feature\n## Fixed\n- Bug fix"
    )
    mock_provider_instance.create_tag.assert_called_once_with(tag="1.2.0")
    mock_provider_instance.create_release.assert_called_once_with(
        body="## Added\n- New feature\n## Fixed\n- Bug fix"
    )


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_merged_to_master(
    mock_getenv, mock_git_provider_class, client, mock_github_payload_merged
):
    payload = mock_github_payload_merged.copy()
    payload["pull_request"]["base"]["ref"] = "master"

    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_pr_body.return_value = "## Modified\n- Updated logic"
    mock_provider_instance.bump_version.return_value = "2.0.0"
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=payload,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_provider_instance.create_tag.assert_called_once_with(tag="2.0.0")
    mock_provider_instance.create_release.assert_called_once()


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_merged_to_feature_branch(
    mock_getenv, mock_git_provider_class, client, mock_github_payload_merged
):
    payload = mock_github_payload_merged.copy()
    payload["pull_request"]["base"]["ref"] = "feature/test"

    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=payload,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_provider_instance.get_pr_body.assert_not_called()
    mock_provider_instance.bump_version.assert_not_called()
    mock_provider_instance.create_tag.assert_not_called()
    mock_provider_instance.create_release.assert_not_called()


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_pr_other_action(
    mock_getenv, mock_git_provider_class, client, mock_github_payload_opened
):
    payload = mock_github_payload_opened.copy()
    payload["action"] = "edited"

    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=payload,
        headers={"x-github-event": "pull_request"},
    )

    assert response.status_code == 200
    mock_provider_instance.get_pr_files.assert_not_called()
    mock_provider_instance.synchronize_changelog.assert_not_called()
    mock_provider_instance.create_pr_body.assert_not_called()


@patch("taglyatelle.exposition.taglyatelle_api.GitProvider")
@patch("os.getenv")
def test_webhook_non_pr_event(mock_getenv, mock_git_provider_class, client):
    payload = {
        "action": "opened",
        "installation": {"id": 12345},
        "repository": {
            "owner": {"login": "test-owner"},
            "name": "test-repo",
        },
    }

    mock_getenv.side_effect = lambda key: {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-4",
    }.get(key)

    mock_provider_instance = MagicMock()
    mock_git_provider_class.return_value = mock_provider_instance

    response = client.post(
        "/taglyatelle/webhooks",
        json=payload,
        headers={"x-github-event": "issues"},
    )

    assert response.status_code == 200
    mock_provider_instance.get_pr_files.assert_not_called()
    mock_provider_instance.get_pr_body.assert_not_called()
