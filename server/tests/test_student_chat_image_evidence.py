from __future__ import annotations

import server.app.agent as agent_module
from server.app.agent import AgentPolicy, AgentRunContext, StudentAIPolicyDecision, _apply_policy_decision_to_classification, classify_agent_request
from server.app.repositories import EmptyMediaRepository, NoopAgentLogRepository, RepositoryProvider
from server.app.schemas import AgentAskRequest, RagSource, RagSourceAsset


class _UnusedRepository:
    pass


def _repositories() -> RepositoryProvider:
    unused = _UnusedRepository()
    return RepositoryProvider(
        content=unused,
        learning=unused,
        review=unused,
        media=EmptyMediaRepository(),
        agent_logs=NoopAgentLogRepository(),
    )


def _context(question: str) -> AgentRunContext:
    request = AgentAskRequest(question=question, chapter_id="CH13")
    return AgentRunContext(
        request=request,
        repositories=_repositories(),
        policy=AgentPolicy(source_path=None, source_excerpt="", course_scope=()),
        classification=classify_agent_request(request),
    )


def test_source_figure_request_stays_on_learning_evidence_rail():
    context = _context("Please explain the Frost diagram evidence for this point.")
    context.policy_decision = StudentAIPolicyDecision(
        mode="needs_platform_evidence",
        reason="mistook figure evidence for a platform resource",
        evidence_required=True,
        allowed_tools=("published_resource_lookup", "rag_search", "curriculum_lookup"),
    )

    _apply_policy_decision_to_classification(context)

    assert context.classification["source_asset_request"] is True
    assert context.classification["resource_request"] is False
    assert context.classification["policy_decision_mode"] == "normal_answer"
    assert "published_resource_lookup" not in context.policy_decision.allowed_tools
    assert any(item["code"] == "policy_resource_veto" for item in context.guardrail_decisions)


def test_source_figure_classification_prefers_rag_over_platform_resources():
    classification = classify_agent_request(_context("Please show the Latimer diagram evidence.").request)

    assert classification["source_asset_request"] is True
    assert classification["resource_request"] is False
    assert classification["rag_preferred"] is True


def test_platform_resource_classification_requires_published_resource_lookup():
    context = _context("\u8fd9\u4e2a\u5b9e\u9a8c\u6709\u6ca1\u6709\u5df2\u53d1\u5e03\u7684\u89c6\u9891\u8d44\u6e90\uff1f")
    context.policy_decision = StudentAIPolicyDecision(
        mode="needs_platform_evidence",
        reason="platform resource availability",
        evidence_required=True,
        allowed_tools=("published_resource_lookup", "rag_search", "curriculum_lookup"),
    )

    _apply_policy_decision_to_classification(context)

    assert context.classification["resource_request"] is True
    assert context.classification["requires_evidence"] is True
    assert context.classification["policy_decision_mode"] == "needs_platform_evidence"


def test_figure_evidence_items_only_reference_existing_image_assets():
    context = _context("Please show the Frost diagram evidence.")
    context.sources = [
        RagSource(
            chunk_id="figure-chunk",
            source_file="figures.md",
            page_number=8,
            text_preview="Frost diagram evidence.",
            content_type="figure",
            caption="Frost diagram",
            assets=[RagSourceAsset(path="figures/frost.png", file_name="frost.png", kind="figure", caption="Frost diagram")],
        )
    ]

    with_asset = agent_module._figure_evidence_items(context, [])
    assert with_asset[0]["asset_count"] == 1
    assert with_asset[0]["asset_files"][0]["markdown"].startswith("![")
    assert "/api/admin/rag-assets?path=" in with_asset[0]["asset_files"][0]["markdown"]

    context.sources = [
        RagSource(
            chunk_id="text-chunk",
            source_file="figures.md",
            page_number=9,
            text_preview="This chunk has no image file.",
            content_type="text",
        )
    ]
    without_asset = agent_module._figure_evidence_items(context, [])
    assert without_asset == []
    assert "![" not in agent_module._source_asset_answer(without_asset)
