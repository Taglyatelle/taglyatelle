"""Unit tests for git factory."""

import pytest
from taglyatelle.git_providers.github_api import GithubAdapter
from taglyatelle.git_providers.core.git_factory import GitProvider
from taglyatelle.git_providers.core.git_registry import git_provider_registry


@pytest.fixture
def github_app(mocker):
    mocker.patch(
        "os.getenv",
        side_effect=lambda k: {
            "APP_ID": "fake_app_id",
            "INSTALLATION_ID": "fake_installation_id",
            "PRIVATE_KEY_PATH": "fake_path",
        }[k],
    )
    mocker.patch("builtins.open", mocker.mock_open(read_data="fake_private_key"))
    mocker.patch("jwt.encode", return_value="jwt_token")
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"token": "access_token"}
    mock_post.return_value = mock_response
    yield GitProvider(git_provider="github", owner="fake_owner", repo="fake_repo")


def test_git_provider_registry():
    assert set(git_provider_registry.keys()) == {"github"}
    assert git_provider_registry["github"] is GithubAdapter


def test_git_provider_get_pr_files(mocker, github_app):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"key": "value"}]
    mock_get.return_value = mock_response
    result = github_app.get_pr_files(pr_number=123)
    assert result == [{"key": "value"}]


def test_git_provider_get_pr_body(mocker, github_app):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"body": "fake_content"}
    mock_get.return_value = mock_response
    assert github_app.get_pr_body(pr_number="fake_number") == "fake_content"


def test_git_provider_create_pr_body(mocker, github_app):
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    assert github_app.create_pr_body(pr_number=1, body="fake_body") is None


def test_git_provider_create_pr_comment(mocker, github_app):
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    assert github_app.create_pr_comment(pr_number=1, message="fake_tag") is None


def test_git_provider_get_current_tag(mocker, github_app):
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"name": "v0.1.0"}]
    mock_get.return_value = mock_response
    assert github_app.get_current_tag() == "v0.1.0"


def test_git_provider_create_tag(mocker, github_app):
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    assert github_app.create_tag("fake_tag") is None


def test_git_provider_create_release(mocker, github_app):
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = "fake_tag"
    github_app.tag = "fake_tag"
    assert github_app.create_release(body="fake_body") is None


def test_git_provider_invoke_llm(mocker, github_app):
    mock_strategy = mocker.Mock()
    mock_strategy.invoke_llm.return_value = "fake_llm_response"
    mocker.patch.object(github_app._builder, "build", return_value=mock_strategy)
    github_app.set_llm_strategy(provider="openai", model="gpt-4", temperature=0.5)
    result = github_app.invoke_llm(prompt="fake_prompt")
    assert result == "fake_llm_response"
    mock_strategy.invoke_llm.assert_called_once_with("fake_prompt")
