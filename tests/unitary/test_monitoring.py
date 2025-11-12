"""Test monitoring tracing functionality."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from taglyatelle.exposition.monitoring import tracing_request


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.headers = {
        "content-type": "application/json",
        "x-github-event": "pull_request",
        "user-agent": "GitHub-Hookshot/test",
    }
    request.body = AsyncMock(return_value=b'{"test": "payload"}')
    return request


def test_tracing_request_enabled_with_request_in_args(mock_request):
    """Test tracing_request decorator when enabled with request in args."""

    @tracing_request(enabled=True)
    async def dummy_handler(self, request):
        return "success"

    with (
        patch("taglyatelle.exposition.monitoring.os.makedirs") as mock_makedirs,
        patch(
            "taglyatelle.exposition.monitoring.aiofiles.open", new_callable=MagicMock
        ) as mock_aiofiles_open,
    ):
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
        mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

        result = asyncio.run(dummy_handler(None, mock_request))

        assert result == "success"
        assert mock_makedirs.called
        assert mock_aiofiles_open.call_count == 2
        assert mock_file.write.call_count == 2


def test_tracing_request_enabled_with_request_in_kwargs(mock_request):
    """Test tracing_request decorator when enabled with request in kwargs."""

    @tracing_request(enabled=True)
    async def dummy_handler(self, request=None):
        return "success"

    with (
        patch("taglyatelle.exposition.monitoring.os.makedirs") as mock_makedirs,
        patch(
            "taglyatelle.exposition.monitoring.aiofiles.open", new_callable=MagicMock
        ) as mock_aiofiles_open,
    ):
        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
        mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

        result = asyncio.run(dummy_handler(None, request=mock_request))

        assert result == "success"
        assert mock_makedirs.called
        assert mock_aiofiles_open.call_count == 2


def test_tracing_request_creates_correct_directory_structure(mock_request):
    """Test that tracing_request creates the correct directory structure."""

    @tracing_request(enabled=True)
    async def dummy_handler(self, request):
        return "success"

    with (
        patch("taglyatelle.exposition.monitoring.os.makedirs") as mock_makedirs,
        patch(
            "taglyatelle.exposition.monitoring.aiofiles.open", new_callable=MagicMock
        ) as mock_aiofiles_open,
        patch("taglyatelle.exposition.monitoring.datetime") as mock_datetime,
    ):
        mock_datetime.now.return_value.strftime.return_value = "2025-10-19_12-00-00"

        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
        mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

        asyncio.run(dummy_handler(None, mock_request))

        mock_makedirs.assert_called_once_with("logs/2025-10-19_12-00-00", exist_ok=True)


def test_tracing_request_saves_headers_correctly(mock_request):
    """Test that tracing_request saves headers correctly."""

    @tracing_request(enabled=True)
    async def dummy_handler(self, request):
        return "success"

    with (
        patch("taglyatelle.exposition.monitoring.os.makedirs"),
        patch(
            "taglyatelle.exposition.monitoring.aiofiles.open", new_callable=MagicMock
        ) as mock_aiofiles_open,
        patch("taglyatelle.exposition.monitoring.datetime") as mock_datetime,
    ):
        mock_datetime.now.return_value.strftime.return_value = "2025-10-19_12-00-00"

        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
        mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

        asyncio.run(dummy_handler(None, mock_request))

        calls = mock_aiofiles_open.call_args_list
        assert any("tracing_headers.json" in str(call) for call in calls)

        write_calls = mock_file.write.call_args_list
        assert len(write_calls) == 2


def test_tracing_request_saves_body_correctly(mock_request):
    """Test that tracing_request saves body correctly."""

    @tracing_request(enabled=True)
    async def dummy_handler(self, request):
        return "success"

    with (
        patch("taglyatelle.exposition.monitoring.os.makedirs"),
        patch(
            "taglyatelle.exposition.monitoring.aiofiles.open", new_callable=MagicMock
        ) as mock_aiofiles_open,
        patch("taglyatelle.exposition.monitoring.datetime") as mock_datetime,
    ):
        mock_datetime.now.return_value.strftime.return_value = "2025-10-19_12-00-00"

        mock_file = AsyncMock()
        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
        mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

        asyncio.run(dummy_handler(None, mock_request))

        calls = mock_aiofiles_open.call_args_list
        assert any("tracing_body.json" in str(call) for call in calls)

        mock_request.body.assert_called_once()
