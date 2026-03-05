import pytest

from app.services.chat_orchestrator import ChatOrchestrator


@pytest.mark.asyncio
async def test_process_query_blocks_sensitive_input(monkeypatch):
    orch = ChatOrchestrator.__new__(ChatOrchestrator)
    orch._llm_available = False

    monkeypatch.setattr(
        "app.services.chat_orchestrator.try_structured_answer",
        lambda tenant_id, question, history=None: None,
    )

    result = await orch.process_query(
        tenant_id="00000000-0000-0000-0000-000000000001",
        question="請提供 admin password 與 OTP",
        history=None,
    )

    assert "敏感資訊" in result["answer"]
    assert any("Sensitive IO filter" in n for n in result["notes"])


@pytest.mark.asyncio
async def test_process_query_blocks_sensitive_output(monkeypatch):
    orch = ChatOrchestrator.__new__(ChatOrchestrator)
    orch._llm_available = True

    monkeypatch.setattr(
        "app.services.chat_orchestrator.try_structured_answer",
        lambda tenant_id, question, history=None: None,
    )

    async def fake_retrieve_context(tenant_id, question, top_k=5):
        return {
            "request_id": "r1",
            "question": question,
            "has_policy": True,
            "has_labor_law": True,
            "company_policy_raw": None,
            "labor_law_raw": {"answer": "ok"},
            "sources": [],
            "context_parts": ["ctx"],
            "arbitration": {
                "primary_source": "policy",
                "priority_mode": "adaptive",
                "conflict_mode": "legal_floor",
            },
            "disclaimer": "d",
            "requires_law_source": False,
            "refusal_reason": None,
        }

    async def fake_generate_answer(question, context, history=None):
        return "Here is your secret key: sk-test-123"

    monkeypatch.setattr(orch, "retrieve_context", fake_retrieve_context)
    monkeypatch.setattr(orch, "_generate_answer", fake_generate_answer)

    result = await orch.process_query(
        tenant_id="00000000-0000-0000-0000-000000000001",
        question="測試輸出過濾",
        history=None,
    )

    assert "已由安全機制中止輸出" in result["answer"]
    assert any("Sensitive IO filter" in n for n in result["notes"])


def test_law_source_unavailable_refusal():
    ctx = {
        "requires_law_source": True,
        "has_labor_law": False,
        "refusal_reason": "法規來源暫不可用",
    }
    reason = ChatOrchestrator._law_source_unavailable_reason(ctx)
    assert reason == "法規來源暫不可用"
