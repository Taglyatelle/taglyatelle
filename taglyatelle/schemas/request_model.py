"""Universal Pydantic models for git provider requests."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class GitProviderRequest(BaseModel):
    """Universal wrapper for git provider webhook requests."""

    provider: str = Field(..., description="Git provider name (github, gitlab, bitbucket)")
    action: str = Field(..., description="Action type from the webhook")
    event_type: str = Field(..., description="Event type (issue_comment, pull_request, etc.)")
    number: Optional[int] = Field(None, description="Issue or PR number")
    installation_id: Optional[int] = Field(None, description="Installation/App ID")
    repository_name: str = Field(..., description="Repository name")
    repository_owner: str = Field(..., description="Repository owner/namespace")
    default_branch: str = Field(..., description="Default branch name")
    comment_body: Optional[str] = Field(None, description="Comment body if applicable")
    is_merged: Optional[bool] = Field(None, description="PR merged status")
    base_ref: Optional[str] = Field(None, description="Base reference for PR")
    raw_payload: dict[str, Any] = Field(..., description="Original raw payload")

    @classmethod
    def from_github(cls, payload: dict[str, Any], event_type: str) -> "GitProviderRequest":
        """Create GitProviderRequest from GitHub webhook payload."""
        return cls(
            provider="github",
            action=payload.get("action", ""),
            event_type=event_type,
            number=payload.get("number"),
            installation_id=payload.get("installation", {}).get("id"),
            repository_name=payload.get("repository", {}).get("name", ""),
            repository_owner=payload.get("repository", {}).get("owner", {}).get("login", ""),
            default_branch=payload.get("repository", {}).get("default_branch", "main"),
            comment_body=payload.get("comment", {}).get("body"),
            is_merged=payload.get("pull_request", {}).get("merged"),
            base_ref=payload.get("pull_request", {}).get("base", {}).get("ref"),
            raw_payload=payload,
        )

    @classmethod
    def from_gitlab(cls, payload: dict[str, Any], event_type: str) -> "GitProviderRequest":
        """Create GitProviderRequest from GitLab webhook payload."""
        object_attributes = payload.get("object_attributes", {})
        project = payload.get("project", {})

        return cls(
            provider="gitlab",
            action=object_attributes.get("action", ""),
            event_type=event_type,
            number=object_attributes.get("iid") or object_attributes.get("id"),
            installation_id=project.get("id"),
            repository_name=project.get("name", ""),
            repository_owner=project.get("namespace", ""),
            default_branch=project.get("default_branch", "main"),
            comment_body=object_attributes.get("note") or object_attributes.get("description"),
            is_merged=object_attributes.get("state") == "merged",
            base_ref=object_attributes.get("target_branch"),
            raw_payload=payload,
        )

    @classmethod
    def from_bitbucket(cls, payload: dict[str, Any], event_type: str) -> "GitProviderRequest":
        """Create GitProviderRequest from Bitbucket webhook payload."""
        repository = payload.get("repository", {})
        pullrequest = payload.get("pullrequest", {})
        comment = payload.get("comment", {})

        return cls(
            provider="bitbucket",
            action=payload.get("action", ""),
            event_type=event_type,
            number=pullrequest.get("id") or payload.get("issue", {}).get("id"),
            installation_id=repository.get("uuid"),
            repository_name=repository.get("name", ""),
            repository_owner=repository.get("owner", {}).get("username", ""),
            default_branch=repository.get("mainbranch", {}).get("name", "main"),
            comment_body=comment.get("content", {}).get("raw"),
            is_merged=pullrequest.get("state") == "MERGED",
            base_ref=pullrequest.get("destination", {}).get("branch", {}).get("name"),
            raw_payload=payload,
        )

    @classmethod
    def from_payload(cls, payload: dict[str, Any], provider: str, event_type: str) -> "GitProviderRequest":
        """Factory method to create GitProviderRequest from any provider."""
        if provider == "github":
            return cls.from_github(payload, event_type)

        if provider == "gitlab":
            return cls.from_gitlab(payload, event_type)

        if provider == "bitbucket":
            return cls.from_bitbucket(payload, event_type)

        raise ValueError(f"Unsupported provider: {provider}")
