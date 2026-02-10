"""Get a GitHub App installation access token."""

import base64
import logging
import os
import time

import jwt
import requests
from dotenv import load_dotenv

from taglyatelle.git_providers.core.git_adapter import GitAdapter

if os.path.exists(".env"):
    load_dotenv()

logging.basicConfig(level=logging.INFO)


class GithubAdapter(GitAdapter):
    """GitHub API configuration."""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        self.tag: str | None = None

        self.app_id = os.getenv("APP_ID")
        self.installation_id = os.getenv("INSTALLATION_ID")
        with open(str(os.getenv("PRIVATE_KEY_PATH"))) as f:
            self.private_key = f.read()

        self.access_token = self._access_token()

    def _access_token(self, duration: int = 60) -> str:
        """
        Get an access token.

        Parameters
        ----------
        duration
            time in seconds for which the token is valid (600 seconds by default)

        Returns
        -------
        access token
        """
        now = int(time.time())
        payload = {"iat": now, "exp": now + (10 * duration), "iss": self.app_id}

        jwt_token = jwt.encode(payload, self.private_key, algorithm="RS256")
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        }

        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        res = requests.post(url, headers=headers)
        access_token = res.json()["token"]

        return access_token

    def _patch_request(self, url: str, body: dict) -> requests.Response:
        """
        Send a PATCH request to the GitHub API.

        Parameters
        ----------
        url
            GitHub API endpoint

        body
            Request body

        Returns
        -------
        Response from the GitHub API
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/{url}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.patch(api_url, headers=headers, json=body)
        return response

    def _post_request(self, url: str, body: dict) -> requests.Response:
        """
        Send a POST request to the GitHub API.

        Parameters
        ----------
        url
            GitHub API endpoint

        body
            Request body

        Returns
        -------
        Response from the GitHub API
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/{url}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.post(api_url, headers=headers, json=body)
        return response

    def _get_request(self, url: str) -> requests.Response:
        """
        Send a GET request to the GitHub API.

        Parameters
        ----------
        url
            GitHub API endpoint

        Returns
        -------
        Response from the GitHub API
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/{url}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.get(api_url, headers=headers)
        return response

    def get_pr_files(self, pr_number: int) -> list[dict[str, str | int]]:
        """
        Get the list of files changed in a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        List of files changed in the pull request
        """
        response = self._get_request(url=f"pulls/{pr_number}/files")
        return response.json()

    def get_pr_body(self, pr_number: int) -> str:
        """
        Get the body/description of a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        The PR body text or None if not present
        """
        response = self._get_request(url=f"pulls/{pr_number}")
        data = response.json()
        return str(data["body"])

    def get_pr_details(self, pr_number: int) -> dict:
        """
        Get the full details of a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        Returns
        -------
        Dictionary containing full PR details including head, base, title, etc.
        """
        response = self._get_request(url=f"pulls/{pr_number}")
        return response.json()

    def create_pr_body(self, pr_number: int, body: str) -> None:
        """
        Fill in the description body of a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        body
            Pull request body text
        """
        data = {"body": body}
        self._patch_request(url=f"pulls/{pr_number}", body=data)
        logging.info("PR body has been successfully updated.")

    def create_pr_comment(self, pr_number: int, message: str) -> None:
        """
        Create a comment on a pull request.

        Parameters
        ----------
        pr_number
            Pull request number

        message
            Comment message
        """
        data = {"body": message}
        self._post_request(url=f"issues/{pr_number}/comments", body=data)
        logging.info("PR comment has been successfully delivered.")

    def get_current_tag(self) -> None | str:
        """
        Get the current tag of the repository.

        Returns
        -------
        Current version of the repository
        """
        response = self._get_request(url="tags")
        tags = response.json()
        if tags:
            return tags[0]["name"]
        return None

    def create_tag(self, tag: str) -> None:
        """
        Create a tag in the repository.

        Parameters
        ----------
        tag
            version of the repo
        """
        self.tag = tag
        data = {"ref": f"refs/tags/{tag}", "sha": "main"}
        self._post_request(url="git/refs", body=data)
        logging.info(f"New Tag {tag} has been successfully delivered.")

    def create_release(self, body: str) -> None:
        """
        Create a release in the repository.

        Parameters
        ----------
        body
            Release notes
        """
        data = {
            "tag_name": self.tag,
            "name": self.tag,
            "body": body,
            "draft": False,
            "prerelease": False,
        }
        self._post_request(url="releases", body=data)
        logging.info(f"New Release for Tag {self.tag} has been successfully delivered.")

    def create_issue(self, title: str, body: str, labels: list[str] | None = None) -> int:
        """
        Create an issue in the repository.

        Parameters
        ----------
        title
            Issue title

        body
            Issue body text

        labels
            List of label names to apply to the issue

        Returns
        -------
        Created issue number
        """
        data: dict[str, str | list[str]] = {"title": title, "body": body}
        if labels is not None:
            data["labels"] = labels

        response = self._post_request(url="issues", body=data)
        issue_data = response.json()
        logging.info(f"Issue #{issue_data.get('number')} has been successfully created.")

        return issue_data["number"]

    def search_issues(self, query: str, state: str = "open", labels: list[str] | None = None) -> list[dict]:
        """
        Search for issues in the repository.

        Parameters
        ----------
        query
            Search query string to match in issue titles

        state
            Issue state: 'open', 'closed', or 'all'

        labels
            Filter by label names

        Returns
        -------
        List of matching issues
        """
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        response = self._get_request(url=f"issues?{self._build_query_string(params)}")
        issues = response.json()

        if query:
            issues = [issue for issue in issues if query.lower() in issue["title"].lower()]

        return issues

    def update_issue(
        self,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> int:
        """
        Update an existing issue.

        Parameters
        ----------
        issue_number
            Issue number to update

        title
            New title (optional)

        body
            New body content (optional)

        state
            New state: 'open' or 'closed' (optional)

        Returns
        -------
        Created issue number
        """
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state

        response = self._patch_request(url=f"issues/{issue_number}", body=data)
        issue_data = response.json()
        logging.info(f"Issue #{issue_data.get('number')} has been successfully updated.")

        return issue_data["number"]

    def _build_query_string(self, params: dict) -> str:
        """
        Build URL query string from parameters.

        Parameters
        ----------
        params
            Dictionary of query parameters

        Returns
        -------
        URL encoded query string
        """
        return "&".join(f"{key}={value}" for key, value in params.items() if value)

    def get_file_content(self, file_path: str, ref: str = "main") -> str | None:
        """
        Get the content of a file from the repository.

        Parameters
        ----------
        file_path
            Path to the file in the repository

        ref
            Git reference (branch, tag, or commit SHA)

        Returns
        -------
        Decoded file content or None if file not found
        """
        response = self._get_request(url=f"contents/{file_path}?ref={ref}")
        if response.status_code == 200:
            content_data = response.json()
            encoded_content = content_data.get("content", "")
            return base64.b64decode(encoded_content).decode("utf-8")
        return None

    def get_repository_tree(self, ref: str = "main") -> list[str]:
        """
        Get the file tree of the repository.

        Parameters
        ----------
        ref
            Git reference (branch, tag, or commit SHA)

        Returns
        -------
        List of file paths in the repository
        """
        response = self._get_request(url=f"git/trees/{ref}?recursive=1")
        if response.status_code == 200:
            tree_data = response.json()
            files = []
            for item in tree_data.get("tree", []):
                if item.get("type") == "blob":
                    files.append(item.get("path", ""))
            return files
        return []
