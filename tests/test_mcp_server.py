"""
MCP Server 工具單元測試

測試 3 個 MCP tools 的邏輯：
  - hr_knowledge_search
  - hr_policy_qa
  - list_documents

使用 httpx mock 模擬 API 回應，不需要實際後端。
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


# ── 匯入 MCP tools ──
from app.mcp_server import hr_knowledge_search, hr_policy_qa, list_documents


# ── Fixtures ──

def _mock_response(status_code: int = 200, json_data=None):
    """建構 mock httpx.Response"""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = json.dumps(json_data or {})
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


# ── hr_knowledge_search 測試 ──

class TestHrKnowledgeSearch:

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        mock_data = [
            {"score": 0.92, "content": "特休假第一年3天", "filename": "handbook.pdf"},
            {"score": 0.85, "content": "年資滿1年有7天", "filename": "leave_policy.docx"},
        ]

        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = _mock_response(200, mock_data)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await hr_knowledge_search("特休假天數")

        assert "特休假" in result
        assert "handbook.pdf" in result
        assert "0.92" in result

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        result = await hr_knowledge_search("")
        assert "錯誤" in result

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = _mock_response(200, [])
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await hr_knowledge_search("不存在的內容xyz")

        assert "未找到" in result

    @pytest.mark.asyncio
    async def test_search_api_error(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = _mock_response(401, {"detail": "Unauthorized"})
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await hr_knowledge_search("特休假")

        assert "API 錯誤" in result

    @pytest.mark.asyncio
    async def test_search_clamps_top_k(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = _mock_response(200, [])
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await hr_knowledge_search("test", top_k=100)

            call_args = client_instance.post.call_args
            sent_json = call_args.kwargs.get("json", {})
            assert sent_json["top_k"] == 10

    @pytest.mark.asyncio
    async def test_search_invalid_mode_defaults_to_hybrid(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = _mock_response(200, [])
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await hr_knowledge_search("test", mode="invalid")

            call_args = client_instance.post.call_args
            sent_json = call_args.kwargs.get("json", {})
            assert sent_json["mode"] == "hybrid"


# ── hr_policy_qa 測試 ──

class TestHrPolicyQa:

    @pytest.mark.asyncio
    async def test_qa_returns_answer(self):
        mock_data = {
            "answer": "依《勞動基準法》第38條，年資滿1年有7天特休假。",
            "sources": [{"title": "《勞動基準法》第38條", "snippet": "年資滿1年..."}],
            "suggestions": ["特休假可以折現嗎？"],
        }

        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.return_value = _mock_response(200, mock_data)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await hr_policy_qa("特休假有幾天？")

        assert "勞動基準法" in result
        assert "第38條" in result
        assert "特休假可以折現嗎" in result

    @pytest.mark.asyncio
    async def test_qa_empty_question(self):
        result = await hr_policy_qa("")
        assert "錯誤" in result

    @pytest.mark.asyncio
    async def test_qa_connection_error(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post.side_effect = httpx.ConnectError("Connection refused")
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await hr_policy_qa("特休假")

        assert "連線錯誤" in result


# ── list_documents 測試 ──

class TestListDocuments:

    @pytest.mark.asyncio
    async def test_list_returns_table(self):
        mock_data = [
            {"filename": "handbook.pdf", "file_type": "pdf", "status": "completed", "chunk_count": 42},
            {"filename": "leave.docx", "file_type": "docx", "status": "completed", "chunk_count": 15},
        ]

        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = _mock_response(200, mock_data)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await list_documents()

        assert "handbook.pdf" in result
        assert "leave.docx" in result
        assert "42" in result

    @pytest.mark.asyncio
    async def test_list_empty(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = _mock_response(200, [])
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await list_documents()

        assert "沒有" in result

    @pytest.mark.asyncio
    async def test_list_clamps_page_size(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = _mock_response(200, [])
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await list_documents(page_size=999)

            call_args = client_instance.get.call_args
            params = call_args.kwargs.get("params", {})
            assert params["limit"] == 50

    @pytest.mark.asyncio
    async def test_list_pagination(self):
        with patch("app.mcp_server.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = _mock_response(200, [])
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await list_documents(page=3, page_size=10)

            call_args = client_instance.get.call_args
            params = call_args.kwargs.get("params", {})
            assert params["skip"] == 20  # (3-1) * 10
