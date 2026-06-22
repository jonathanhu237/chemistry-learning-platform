from __future__ import annotations

from dataclasses import replace

from server.app.infrastructure.settings import Settings
import server.app.domains.questions.workbench as question_workbench_service
from server.app.domains.questions.workbench import _question_workbench_rag_gate


def _rag_gate_settings(**overrides):
    return replace(
        Settings(),
        rag_hybrid_bge_enabled=True,
        rag_query_generation_enabled=True,
        rag_bge_service_url="http://bge.local",
        **overrides,
    )


def test_question_workbench_rag_gate_blocks_when_rag_access_disabled(monkeypatch):
    monkeypatch.setattr(question_workbench_service, "get_settings", lambda: _rag_gate_settings())
    monkeypatch.setattr(question_workbench_service, "ai_feature_enabled", lambda name: False if name == "rag_access_enabled" else True)

    gate = _question_workbench_rag_gate()

    assert gate["healthy"] is False
    assert gate["reason_code"] == "rag_disabled"


def test_question_workbench_rag_gate_allows_when_bge_metrics_are_ok(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'{"ok": true, "service": "bge-rag"}'

    monkeypatch.setattr(question_workbench_service, "get_settings", lambda: _rag_gate_settings())
    monkeypatch.setattr(question_workbench_service, "ai_feature_enabled", lambda name: True)
    monkeypatch.setattr(question_workbench_service.urllib.request, "urlopen", lambda url, timeout: FakeResponse())

    gate = _question_workbench_rag_gate()

    assert gate["healthy"] is True
    assert gate["bge_status"] == "healthy"
    assert gate["bge_metrics"]["service"] == "bge-rag"


def test_question_workbench_rag_gate_blocks_degraded_bge_metrics(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'{"ok": false, "service": "bge-rag"}'

    monkeypatch.setattr(question_workbench_service, "get_settings", lambda: _rag_gate_settings())
    monkeypatch.setattr(question_workbench_service, "ai_feature_enabled", lambda name: True)
    monkeypatch.setattr(question_workbench_service.urllib.request, "urlopen", lambda url, timeout: FakeResponse())

    gate = _question_workbench_rag_gate()

    assert gate["healthy"] is False
    assert gate["reason_code"] == "bge_degraded"
    assert gate["bge_status"] == "degraded"
