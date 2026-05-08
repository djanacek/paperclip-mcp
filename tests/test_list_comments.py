"""Tests for the list_comments MCP tool."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import paperclip_mcp.server as srv


def _mock_response(status_code: int, json_data: object) -> MagicMock:
    """Build a minimal httpx.Response stand-in."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = b"x"
    resp.json.return_value = json_data
    resp.text = str(json_data)
    if status_code >= 400:
        from httpx import HTTPStatusError, Request, Response
        real_resp = MagicMock(spec=Response)
        real_resp.status_code = status_code
        real_resp.text = str(json_data)
        resp.raise_for_status.side_effect = HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(spec=Request),
            response=real_resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


def _patch_client(response: MagicMock):
    """Context manager that replaces httpx.AsyncClient with a mock."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.request = AsyncMock(return_value=response)
    return patch("paperclip_mcp.server.httpx.AsyncClient", return_value=mock_client), mock_client


SAMPLE_COMMENTS = [
    {
        "id": "comment-1",
        "body": "First comment on the issue.",
        "author": {"id": "agent-abc", "name": "Walter"},
        "createdAt": "2026-05-07T10:00:00.000Z",
        "parentId": None,
    },
    {
        "id": "comment-2",
        "body": "Follow-up with more details.",
        "author": {"id": "agent-xyz", "name": "Priya"},
        "createdAt": "2026-05-07T11:30:00.000Z",
        "parentId": None,
    },
]


class TestListCommentsHappyPath:
    """list_comments returns a list of comment objects for a valid issue."""

    async def test_returns_comment_list(self):
        response = _mock_response(200, SAMPLE_COMMENTS)
        ctx, mock_client = _patch_client(response)
        with ctx:
            result = await srv.list_comments("COVA-27")

        assert result == SAMPLE_COMMENTS

    async def test_request_uses_correct_path(self):
        response = _mock_response(200, SAMPLE_COMMENTS)
        ctx, mock_client = _patch_client(response)
        with ctx:
            await srv.list_comments("COVA-27")

        call_args = mock_client.request.call_args
        assert call_args.args[0] == "GET"
        assert call_args.args[1].endswith("/issues/COVA-27/comments")

    async def test_default_params(self):
        response = _mock_response(200, SAMPLE_COMMENTS)
        ctx, mock_client = _patch_client(response)
        with ctx:
            await srv.list_comments("COVA-27")

        call_args = mock_client.request.call_args
        params = call_args.kwargs.get("params") or {}
        assert params["limit"] == 50
        assert params["order"] == "asc"
        assert "after" not in params

    async def test_custom_limit_is_clamped(self):
        response = _mock_response(200, [])
        ctx, mock_client = _patch_client(response)
        with ctx:
            await srv.list_comments("COVA-27", limit=999)

        params = mock_client.request.call_args.kwargs.get("params") or {}
        assert params["limit"] == 500

    async def test_limit_minimum_is_one(self):
        response = _mock_response(200, [])
        ctx, mock_client = _patch_client(response)
        with ctx:
            await srv.list_comments("COVA-27", limit=0)

        params = mock_client.request.call_args.kwargs.get("params") or {}
        assert params["limit"] == 1


class TestListCommentsEmptyThread:
    """list_comments returns an empty list when the issue has no comments."""

    async def test_empty_list_returned(self):
        response = _mock_response(200, [])
        ctx, mock_client = _patch_client(response)
        with ctx:
            result = await srv.list_comments("COVA-99")

        assert result == []

    async def test_no_error_on_empty(self):
        response = _mock_response(200, [])
        ctx, mock_client = _patch_client(response)
        with ctx:
            result = await srv.list_comments("COVA-99")

        assert not isinstance(result, dict) or not result.get("isError")


class TestListCommentsPagination:
    """list_comments passes the after cursor correctly for pagination."""

    async def test_after_cursor_included_in_params(self):
        response = _mock_response(200, [SAMPLE_COMMENTS[1]])
        ctx, mock_client = _patch_client(response)
        with ctx:
            await srv.list_comments("COVA-27", after="comment-1")

        params = mock_client.request.call_args.kwargs.get("params") or {}
        assert params["after"] == "comment-1"

    async def test_empty_after_omitted_from_params(self):
        response = _mock_response(200, SAMPLE_COMMENTS)
        ctx, mock_client = _patch_client(response)
        with ctx:
            await srv.list_comments("COVA-27", after="")

        params = mock_client.request.call_args.kwargs.get("params") or {}
        assert "after" not in params

    async def test_pagination_sequence(self):
        """Simulates two successive pages of comments."""
        page1 = _mock_response(200, [SAMPLE_COMMENTS[0]])
        page2 = _mock_response(200, [SAMPLE_COMMENTS[1]])

        ctx1, client1 = _patch_client(page1)
        with ctx1:
            first_page = await srv.list_comments("COVA-27", limit=1)

        last_id = first_page[-1]["id"]

        ctx2, client2 = _patch_client(page2)
        with ctx2:
            second_page = await srv.list_comments("COVA-27", limit=1, after=last_id)

        params = client2.request.call_args.kwargs.get("params") or {}
        assert params["after"] == last_id
        assert second_page == [SAMPLE_COMMENTS[1]]


class TestListCommentsInvalidIssueId:
    """list_comments returns a structured error when the issue does not exist."""

    async def test_404_returns_error_dict(self):
        response = _mock_response(404, {"error": "Issue not found"})
        ctx, mock_client = _patch_client(response)
        with ctx:
            result = await srv.list_comments("DOES-NOT-EXIST")

        assert isinstance(result, dict)
        assert result.get("isError") is True
        assert result.get("status") == 404

    async def test_error_message_includes_status(self):
        response = _mock_response(404, {"error": "Issue not found"})
        ctx, mock_client = _patch_client(response)
        with ctx:
            result = await srv.list_comments("DOES-NOT-EXIST")

        assert "404" in result.get("message", "")

    async def test_existing_tools_unaffected(self):
        """Regression: list_issues still works after list_comments is defined."""
        response = _mock_response(200, {"issues": []})
        ctx, mock_client = _patch_client(response)
        with ctx:
            result = await srv.list_issues()

        assert result == {"issues": []}
        call_args = mock_client.request.call_args
        assert "/companies/" in call_args.args[1]
        assert "/issues" in call_args.args[1]
