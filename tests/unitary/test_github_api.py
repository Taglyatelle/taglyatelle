"""Unit tests for github api."""

import pytest
from taglyatelle.git_providers.github_api import GithubAdapter


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
    yield GithubAdapter(owner="fake_owner", repo="fake_repo")


def test_access_token(github_app):
    assert github_app._access_token() == "access_token"


def test_get_pr_files(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"key": "value"}]
    mock_get.return_value = mock_response
    assert github_app.get_pr_files(pr_number="fake_number") == [{"key": "value"}]


def test_get_pr_body(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"body": "fake_content"}
    mock_get.return_value = mock_response
    assert github_app.get_pr_body(pr_number="fake_number") == "fake_content"


def test_create_pr_body(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    assert github_app.create_pr_body(pr_number=1, body="fake_body") is None


def test_create_pr_comment(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    assert github_app.create_pr_comment(pr_number=1, message="fake_tag") is None


def test_get_current_tag(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"name": "v0.1.0"}]
    mock_get.return_value = mock_response
    assert github_app.get_current_tag() == "v0.1.0"


def test_create_tag(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    assert github_app.create_tag("fake_tag") is None


def test_create_release(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_request = mocker.Mock()
    mock_request.post.return_value.json.return_value = None
    github_app.tag = "fake_tag"
    assert github_app.create_release(body="fake_body") is None


def test_create_issue(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"number": 42}
    mock_post.return_value = mock_response
    results = github_app.create_issue(title="fake_title", body="fake_body")
    assert results == 42


def test_create_issue_with_labels(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_post = mocker.patch("requests.post")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"number": 43}
    mock_post.return_value = mock_response
    results = github_app.create_issue(title="fake", body="fake", labels=["bug"])
    assert results == 43


def test_get_file_content(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"content": "ZmFrZV9jb250ZW50"}
    mock_get.return_value = mock_response
    assert github_app.get_file_content(file_path="fake_path") == "fake_content"


def test_search_issues(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"number": 1, "title": "Bug in feature"},
        {"number": 2, "title": "Feature request"},
    ]
    mock_get.return_value = mock_response
    results = github_app.search_issues(query="bug", state="open")
    assert len(results) == 1
    assert results[0]["number"] == 1


def test_search_issues_with_labels(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"number": 3, "title": "Critical bug"},
    ]
    mock_get.return_value = mock_response
    results = github_app.search_issues(query="bug", labels=["critical"])
    assert len(results) == 1


def test_update_issue(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_patch = mocker.patch("requests.patch")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"number": 1}
    mock_patch.return_value = mock_response
    results = github_app.update_issue(issue_number=1, title="new_title")
    assert results == 1


def test_update_issue_full(mocker, github_app):
    mocker.patch.object(github_app, "_access_token", return_value="jwt_token")
    mock_patch = mocker.patch("requests.patch")
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"number": 2}
    mock_patch.return_value = mock_response
    result = github_app.update_issue(
        issue_number=2, title="new_title", body="new_body", state="closed"
    )
    assert result == 2
