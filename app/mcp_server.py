"""
UniHR MCP Server — Model Context Protocol 伺服器

讓外部 AI 助手（Claude、GPT、Copilot 等）透過 MCP 協定存取 UniHR 知識庫。

暴露 3 個核心工具：
  1. hr_knowledge_search  — 搜尋公司知識庫（hybrid: 語意 + BM25）
  2. hr_policy_qa         — HR 政策問答（RAG：檢索 + LLM 生成）
  3. list_documents       — 列出已上傳文件

啟動方式：
  python -m app.mcp_server

或在 MCP client 設定中指定：
  {
    "mcpServers": {
      "unihr": {
        "command": "python",
        "args": ["-m", "app.mcp_server"],
        "env": {
          "UNIHR_API_URL": "http://localhost:8000",
          "UNIHR_API_TOKEN": "your-jwt-token"
        }
      }
    }
  }
"""

import os
import logging
import httpx

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# ── 設定 ──
UNIHR_API_URL = os.environ.get("UNIHR_API_URL", "http://localhost:8000")
UNIHR_API_TOKEN = os.environ.get("UNIHR_API_TOKEN", "")
API_TIMEOUT = 30  # 秒


def _api_headers() -> dict:
    """建構 API 請求標頭"""
    headers = {"Content-Type": "application/json"}
    if UNIHR_API_TOKEN:
        headers["Authorization"] = f"Bearer {UNIHR_API_TOKEN}"
    return headers


def _api_url(path: str) -> str:
    """組合完整 API URL"""
    base = UNIHR_API_URL.rstrip("/")
    return f"{base}/api/v1{path}"


# ── MCP Server ──
mcp = FastMCP(
    "UniHR",
    instructions=(
        "UniHR 是台灣企業人資知識管理平台。"
        "使用這些工具來搜尋公司內部規章、查詢勞動法規、"
        "或列出已上傳的 HR 文件。所有回答皆為繁體中文。"
    ),
)


@mcp.tool()
async def hr_knowledge_search(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid",
) -> str:
    """
    搜尋公司 HR 知識庫。

    使用混合檢索（語意向量 + BM25 關鍵字）搜尋公司內部規章。
    回傳最相關的文件片段，包含來源檔名與相關度分數。

    Args:
        query: 搜尋查詢（例如「特休假天數」、「加班費計算」）
        top_k: 回傳前幾筆結果（預設 5，最多 10）
        mode: 檢索模式 - hybrid（混合）、semantic（語意）、keyword（關鍵字）
    """
    if not query.strip():
        return "錯誤：查詢不能為空"

    top_k = min(max(1, top_k), 10)
    if mode not in ("hybrid", "semantic", "keyword"):
        mode = "hybrid"

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.post(
                _api_url("/kb/search"),
                headers=_api_headers(),
                json={"query": query, "top_k": top_k, "mode": mode},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        return f"API 錯誤（{e.response.status_code}）：{e.response.text[:200]}"
    except Exception as e:
        return f"連線錯誤：{e}"

    results = data if isinstance(data, list) else data.get("results", [])
    if not results:
        return f"未找到與「{query}」相關的結果。請嘗試不同的關鍵字。"

    parts = [f"## 搜尋結果：{query}\n"]
    for i, r in enumerate(results, 1):
        score = r.get("score", 0)
        content = r.get("content", "")[:500]
        filename = r.get("filename", "未知")
        parts.append(
            f"### {i}. {filename}（相關度：{score:.2f}）\n{content}\n"
        )
    return "\n".join(parts)


@mcp.tool()
async def hr_policy_qa(
    question: str,
    top_k: int = 3,
) -> str:
    """
    HR 政策問答 — 使用 RAG 技術回答人資問題。

    系統會：
    1. 搜尋公司內部規章
    2. 查詢台灣勞動法規
    3. 使用 AI 生成結合兩者的回答

    適用問題範例：
    - 「特休假有幾天？」
    - 「加班費怎麼算？」
    - 「試用期可以解僱嗎？」
    - 「喪假可以請幾天？」

    Args:
        question: 人資相關問題（繁體中文）
        top_k: 檢索文件數量（預設 3）
    """
    if not question.strip():
        return "錯誤：問題不能為空"

    top_k = min(max(1, top_k), 5)

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.post(
                _api_url("/chat"),
                headers=_api_headers(),
                json={"question": question, "top_k": top_k},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        return f"API 錯誤（{e.response.status_code}）：{e.response.text[:200]}"
    except Exception as e:
        return f"連線錯誤：{e}"

    answer = data.get("answer", "")
    sources = data.get("sources", [])
    suggestions = data.get("suggestions", [])

    parts = [answer]

    if sources:
        parts.append("\n---\n**參考來源：**")
        for s in sources[:5]:
            title = s.get("title", s.get("filename", ""))
            snippet = s.get("snippet", "")[:100]
            if title:
                parts.append(f"- {title}: {snippet}")

    if suggestions:
        parts.append("\n**你可能還想問：**")
        for s in suggestions[:3]:
            parts.append(f"- {s}")

    return "\n".join(parts)


@mcp.tool()
async def list_documents(
    page: int = 1,
    page_size: int = 20,
) -> str:
    """
    列出公司已上傳的 HR 文件。

    顯示文件名稱、類型、狀態、上傳時間。
    可用來了解知識庫中有哪些文件可供查詢。

    Args:
        page: 頁碼（預設 1）
        page_size: 每頁筆數（預設 20，最多 50）
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 50)

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            resp = await client.get(
                _api_url("/documents/"),
                headers=_api_headers(),
                params={"skip": (page - 1) * page_size, "limit": page_size},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        return f"API 錯誤（{e.response.status_code}）：{e.response.text[:200]}"
    except Exception as e:
        return f"連線錯誤：{e}"

    docs = data if isinstance(data, list) else data.get("documents", data.get("items", []))
    if not docs:
        return "目前沒有已上傳的文件。"

    parts = [f"## 文件列表（第 {page} 頁）\n"]
    parts.append("| # | 檔名 | 類型 | 狀態 | 切片數 |")
    parts.append("|---|------|------|------|--------|")
    for i, d in enumerate(docs, (page - 1) * page_size + 1):
        filename = d.get("filename", "未知")
        file_type = d.get("file_type", "-")
        doc_status = d.get("status", "-")
        chunks = d.get("chunk_count", 0) or 0
        parts.append(f"| {i} | {filename} | {file_type} | {doc_status} | {chunks} |")

    return "\n".join(parts)


# ── 啟動入口 ──
if __name__ == "__main__":
    mcp.run()
