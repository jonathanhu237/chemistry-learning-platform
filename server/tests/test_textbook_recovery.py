from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import scripts.bootstrap_production_seed as bootstrap_seed
import scripts.import_precomputed_textbook_rag as seed_import
import scripts.rebuild_online_textbook_projections as rebuild_script
from server.app.domains.textbook_ingestion.contracts import ExtractionMethod, StableChunk
from server.app.domains.textbook_ingestion.recovery import (
    RetainedOnlineTextbook,
    TextbookRecoveryError,
    reproject_online_textbooks,
    validate_reprojection_configuration,
)
from server.app.infrastructure.settings import Settings


def _chunk() -> StableChunk:
    return StableChunk(
        chunk_id="chunk-1",
        document_id="tbk-1",
        document_version=2,
        chunk_index=1,
        text="retained PostgreSQL chemistry text",
        markdown="retained PostgreSQL chemistry text",
        page_start=1,
        page_end=1,
        section_title="Section",
        section_path=["Chapter", "Section"],
        content_type="text",
        content_hash="hash-1",
        extraction_method=ExtractionMethod.NATIVE,
    )


def _document(*, expected_model: str = "embedding-v1") -> RetainedOnlineTextbook:
    return RetainedOnlineTextbook(
        document_id="tbk-1",
        logical_textbook_key="chemistry",
        document_version=2,
        title="Chemistry",
        publication_status="published",
        processing_fingerprint="fingerprint-v1",
        active_projection_run_id="old-run",
        expected_embedding_model=expected_model,
        expected_embedding_dimension=3,
        chunks=(_chunk(),),
    )


@dataclass(frozen=True)
class _EmbeddingResult:
    vectors: list[list[float]]


class _Embedder:
    model = "embedding-v1"

    def __init__(self) -> None:
        self.calls: list[list[StableChunk]] = []

    def embed_chunks(self, chunks: list[StableChunk] | tuple[StableChunk, ...]) -> _EmbeddingResult:
        self.calls.append(list(chunks))
        return _EmbeddingResult(vectors=[[0.1, 0.2, 0.3] for _ in chunks])


class _Projector:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.cleanup_calls: list[tuple[str, str]] = []
        self.projection_run_id = ""

    def project(
        self,
        chunks: list[StableChunk] | tuple[StableChunk, ...],
        embeddings: list[list[float]],
        *,
        embedding_model: str,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "chunks": list(chunks),
                "embeddings": embeddings,
                "embedding_model": embedding_model,
            }
        )
        return {
            "index_verified": True,
            "indexed_chunks": len(chunks),
            "projection_run_id": self.projection_run_id,
        }

    def delete_projection_run(
        self,
        document_id: str,
        projection_run_id: str,
    ) -> dict[str, object]:
        self.cleanup_calls.append((document_id, projection_run_id))
        return {"deleted": 1, "projection_run_id": projection_run_id}


def test_reprojection_recomputes_vectors_and_verifies_every_postgres_chunk() -> None:
    embedder = _Embedder()
    projector = _Projector()
    run_ids: list[str] = []
    committed_runs: list[str] = []

    def projector_factory(_document: RetainedOnlineTextbook, run_id: str) -> _Projector:
        run_ids.append(run_id)
        projector.projection_run_id = run_id
        return projector

    result = reproject_online_textbooks(
        [_document()],
        embedder=embedder,
        embedding_dimension=3,
        projector_factory=projector_factory,
        run_committer=lambda _document, run_id, _projection: committed_runs.append(run_id),
    )

    assert result["ok"] is True
    assert result["documents"] == 1
    assert result["chunks"] == 1
    assert embedder.calls == [[_chunk()]]
    assert projector.calls[0]["embeddings"] == [[0.1, 0.2, 0.3]]
    assert projector.calls[0]["embedding_model"] == "embedding-v1"
    assert run_ids[0].startswith("recovery-")
    assert committed_runs == run_ids


def test_reprojection_refuses_changed_embedding_contract_before_provider_call() -> None:
    embedder = _Embedder()

    with pytest.raises(TextbookRecoveryError) as raised:
        reproject_online_textbooks(
            [_document(expected_model="different-model")],
            embedder=embedder,
            embedding_dimension=3,
            projector_factory=lambda _document, _run_id: _Projector(),
            run_committer=lambda _document, _run_id, _projection: None,
        )

    assert raised.value.reason == "embedding_model_changed"
    assert embedder.calls == []


def test_reprojection_does_not_activate_an_unverified_projection_run() -> None:
    embedder = _Embedder()
    projector = _Projector()
    projector.projection_run_id = "wrong-run"
    committed: list[str] = []

    with pytest.raises(TextbookRecoveryError) as raised:
        reproject_online_textbooks(
            [_document()],
            embedder=embedder,
            embedding_dimension=3,
            projector_factory=lambda _document, _run_id: projector,
            run_committer=lambda _document, run_id, _projection: committed.append(run_id),
        )

    assert raised.value.reason == "online_textbook_projection_run_mismatch"
    assert committed == []
    assert len(projector.cleanup_calls) == 1
    assert projector.cleanup_calls[0][0] == "tbk-1"
    assert projector.cleanup_calls[0][1].startswith("recovery-")


def test_reprojection_removes_exact_run_when_database_activation_fails() -> None:
    embedder = _Embedder()
    projector = _Projector()

    def projector_factory(_document: RetainedOnlineTextbook, run_id: str) -> _Projector:
        projector.projection_run_id = run_id
        return projector

    def fail_activation(*_args: Any) -> None:
        raise RuntimeError("activation failed")

    with pytest.raises(RuntimeError, match="activation failed"):
        reproject_online_textbooks(
            [_document()],
            embedder=embedder,
            embedding_dimension=3,
            projector_factory=projector_factory,
            run_committer=fail_activation,
        )

    assert len(projector.cleanup_calls) == 1
    assert projector.cleanup_calls[0][0] == "tbk-1"
    assert projector.cleanup_calls[0][1] == projector.projection_run_id


def test_reprojection_surfaces_cleanup_failure_after_activation_failure() -> None:
    embedder = _Embedder()

    class _CleanupFailureProjector(_Projector):
        def delete_projection_run(
            self,
            document_id: str,
            projection_run_id: str,
        ) -> dict[str, object]:
            self.cleanup_calls.append((document_id, projection_run_id))
            raise RuntimeError("cleanup failed")

    projector = _CleanupFailureProjector()

    def projector_factory(_document: RetainedOnlineTextbook, run_id: str) -> _Projector:
        projector.projection_run_id = run_id
        return projector

    def fail_activation(*_args: Any) -> None:
        raise RuntimeError("activation failed")

    with pytest.raises(TextbookRecoveryError) as raised:
        reproject_online_textbooks(
            [_document()],
            embedder=embedder,
            embedding_dimension=3,
            projector_factory=projector_factory,
            run_committer=fail_activation,
        )

    assert raised.value.reason == "online_textbook_reprojection_cleanup_failed"
    assert raised.value.details["original_reason"] == "RuntimeError"
    assert len(projector.cleanup_calls) == 1


def _bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(
        json.dumps(
            {
                "exported_docs": 1,
                "embedding_model": "embedding-v1",
                "embedding_dimension": 3,
            }
        ),
        encoding="utf-8",
    )
    return bundle


def test_operator_target_defaults_to_db_backed_effective_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    effective = type(
        "EffectiveSettings",
        (),
        {
            "textbook_rag_elasticsearch_url": "http://runtime-es.test:9200/",
            "textbook_rag_elasticsearch_index": "runtime-textbooks",
        },
    )()
    calls: list[str] = []
    monkeypatch.setattr(
        seed_import,
        "_effective_ingestion_settings",
        lambda: calls.append("effective") or effective,
    )

    target = seed_import.resolve_elasticsearch_target()

    assert target.base_url == "http://runtime-es.test:9200"
    assert target.index == "runtime-textbooks"
    assert calls == ["effective"]


def test_operator_target_explicit_flags_override_without_db_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        seed_import,
        "_effective_ingestion_settings",
        lambda: pytest.fail("explicit target must not query effective settings"),
    )

    target = seed_import.resolve_elasticsearch_target(
        es_url="https://operator:secret@override-es.test:9243/?api_key=also-secret",
        index="override-textbooks",
    )

    assert target.base_url == "https://operator:secret@override-es.test:9243/?api_key=also-secret"
    assert target.index == "override-textbooks"
    assert target.display_url == "https://***@override-es.test:9243/"


def test_precomputed_import_cli_resolves_omitted_target_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = seed_import.ElasticsearchTarget(
        base_url="http://runtime-es.test:9200",
        index="runtime-textbooks",
    )
    resolutions: list[dict[str, str | None]] = []
    imports: list[dict[str, Any]] = []
    monkeypatch.setattr(
        seed_import,
        "resolve_elasticsearch_target",
        lambda **kwargs: resolutions.append(dict(kwargs)) or target,
    )
    monkeypatch.setattr(
        seed_import,
        "import_precomputed_index",
        lambda **kwargs: imports.append(dict(kwargs)) or {"ok": True},
    )
    monkeypatch.setattr("sys.argv", ["import_precomputed_textbook_rag.py", "--dry-run"])

    seed_import.main()

    assert resolutions == [{"es_url": None, "index": None}]
    assert imports[0]["base_url"] == target.base_url
    assert imports[0]["index"] == target.index


def test_rebuild_cli_resolves_omitted_target_for_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = seed_import.ElasticsearchTarget(
        base_url="http://runtime-es.test:9200",
        index="runtime-textbooks",
    )
    resolutions: list[dict[str, str | None]] = []
    monkeypatch.setattr(
        rebuild_script,
        "resolve_elasticsearch_target",
        lambda **kwargs: resolutions.append(dict(kwargs)) or target,
    )
    monkeypatch.setattr(
        rebuild_script,
        "load_online_textbooks_for_reprojection",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr("sys.argv", ["rebuild_online_textbook_projections.py", "--dry-run"])

    rebuild_script.main()

    assert resolutions == [{"es_url": None, "index": None}]


def test_precomputed_bundle_identity_is_independent_of_target_index(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    manifest["index"] = "bundle-source-index"
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (bundle / "bundle-source-index.documents.jsonl").write_text(
        json.dumps(
            {
                "_id": "seed-1",
                "_source": {
                    "embedding": [0.1, 0.2, 0.3],
                    "embedding_model": "embedding-v1",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = seed_import.import_precomputed_index(
        base_url="http://runtime-es.test:9200",
        bundle_dir=bundle,
        index="runtime-textbooks",
        recreate=False,
        batch_size=10,
        replicas=0,
        timeout=1,
        dry_run=True,
    )

    assert result["ok"] is True
    assert result["elasticsearch_url"] == "http://runtime-es.test:9200"
    assert result["index"] == "runtime-textbooks"
    assert result["bundle_index"] == "bundle-source-index"
    assert result["indexed_documents"] == 1


def test_seed_recreate_fails_before_es_mutation_when_online_documents_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutated = False

    def unexpected_mutation(**_kwargs: Any) -> None:
        nonlocal mutated
        mutated = True

    monkeypatch.setattr(seed_import, "_create_index", unexpected_mutation)
    result = seed_import.import_precomputed_index(
        base_url="http://es.invalid",
        bundle_dir=_bundle(tmp_path),
        index="shared-textbooks",
        recreate=True,
        batch_size=10,
        replicas=0,
        timeout=1,
        dry_run=False,
        online_inventory_loader=lambda: {
            "documents": 1,
            "chunks": 1,
            "by_status": {"published": {"documents": 1, "chunks": 1}},
        },
    )

    assert result["ok"] is False
    assert "refusing to recreate" in result["failures"][0]
    assert mutated is False


def test_online_rebuild_flag_requires_explicit_shared_index_recreate(tmp_path: Path) -> None:
    result = seed_import.import_precomputed_index(
        base_url="http://es.invalid",
        bundle_dir=_bundle(tmp_path),
        index="shared-textbooks",
        recreate=False,
        batch_size=10,
        replicas=0,
        timeout=1,
        dry_run=True,
        rebuild_online_projections=True,
    )

    assert result["ok"] is False
    assert result["failures"] == ["--rebuild-online-projections requires --recreate"]


def test_explicit_seed_recreate_restores_online_projections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight_calls: list[str] = []
    rebuild_calls: list[str] = []
    monkeypatch.setattr(seed_import, "_create_index", lambda **_kwargs: None)
    monkeypatch.setattr(
        seed_import,
        "_iter_documents",
        lambda _bundle, _index: iter(
            [
                {
                    "_id": "seed-1",
                    "_source": {
                        "embedding": [0.1, 0.2, 0.3],
                        "embedding_model": "embedding-v1",
                    },
                }
            ]
        ),
    )
    monkeypatch.setattr(seed_import, "_bulk", lambda *_args, **_kwargs: {"errors": False})
    monkeypatch.setattr(seed_import, "_request", lambda *_args, **_kwargs: {})

    result = seed_import.import_precomputed_index(
        base_url="http://es.invalid",
        bundle_dir=_bundle(tmp_path),
        index="shared-textbooks",
        recreate=True,
        batch_size=10,
        replicas=0,
        timeout=1,
        dry_run=False,
        rebuild_online_projections=True,
        online_inventory_loader=lambda: {
            "documents": 1,
            "chunks": 1,
            "by_status": {"inactive": {"documents": 1, "chunks": 1}},
        },
        online_reprojection_preflight=lambda: preflight_calls.append("preflight")
        or {"embedding_model": "embedding-v1", "embedding_dimension": 3},
        online_rebuilder=lambda: rebuild_calls.append("rebuild")
        or {"ok": True, "documents": 1, "chunks": 1},
    )

    assert result["ok"] is True
    assert preflight_calls == ["preflight"]
    assert rebuild_calls == ["rebuild"]
    assert result["online_reprojection"]["documents"] == 1


def test_seed_recreate_rejects_bundle_contract_before_index_deletion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutations: list[str] = []
    monkeypatch.setattr(
        seed_import,
        "_create_index",
        lambda **_kwargs: mutations.append("index_deleted"),
    )

    result = seed_import.import_precomputed_index(
        base_url="http://es.invalid",
        bundle_dir=_bundle(tmp_path),
        index="shared-textbooks",
        recreate=True,
        batch_size=10,
        replicas=0,
        timeout=1,
        dry_run=False,
        rebuild_online_projections=True,
        online_inventory_loader=lambda: {
            "documents": 1,
            "chunks": 1,
            "by_status": {"published": {"documents": 1, "chunks": 1}},
        },
        online_reprojection_preflight=lambda: {
            "embedding_model": "embedding-v2",
            "embedding_dimension": 4,
        },
    )

    assert result["ok"] is False
    assert any("embedding model" in failure for failure in result["failures"])
    assert any("embedding dimension" in failure for failure in result["failures"])
    assert mutations == []


def test_preflight_only_checks_online_inventory_without_es_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutations: list[str] = []
    monkeypatch.setattr(
        seed_import,
        "_create_index",
        lambda **_kwargs: mutations.append("index_deleted"),
    )

    result = seed_import.import_precomputed_index(
        base_url="http://es.invalid",
        bundle_dir=_bundle(tmp_path),
        index="shared-textbooks",
        recreate=True,
        batch_size=10,
        replicas=0,
        timeout=1,
        dry_run=False,
        preflight_only=True,
        online_inventory_loader=lambda: {
            "documents": 0,
            "chunks": 0,
            "by_status": {},
        },
    )

    assert result["ok"] is True
    assert result["preflight_only"] is True
    assert result["scanned_documents"] == 0
    assert mutations == []


def test_bootstrap_runs_shared_index_preflight_before_postgres_seed_mutations(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands: list[list[str]] = []
    target = seed_import.ElasticsearchTarget(
        base_url="http://runtime-es.test:9200",
        index="runtime-textbooks",
    )
    monkeypatch.setattr(
        bootstrap_seed,
        "_run",
        lambda args, **_kwargs: commands.append(list(args)),
    )
    monkeypatch.setattr(
        bootstrap_seed,
        "resolve_elasticsearch_target",
        lambda **_kwargs: target,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "bootstrap_production_seed.py",
            "--skip-identities",
            "--skip-media",
            "--skip-validation",
            "--rebuild-online-projections",
        ],
    )

    bootstrap_seed.main()

    preflight_index = next(
        index for index, command in enumerate(commands) if "--preflight-only" in command
    )
    first_seed_mutation = next(
        index
        for index, command in enumerate(commands)
        if command[0] == "scripts/publish_reviewed_curriculum.py"
    )
    actual_import_index = max(
        index
        for index, command in enumerate(commands)
        if command[0] == "scripts/import_precomputed_textbook_rag.py"
    )

    assert commands[0] == ["scripts/apply_migrations.py"]
    assert preflight_index < first_seed_mutation < actual_import_index
    assert "--rebuild-online-projections" in commands[preflight_index]
    for command_index in (preflight_index, actual_import_index):
        assert commands[command_index][
            commands[command_index].index("--es-url") + 1
        ] == target.base_url
        assert commands[command_index][
            commands[command_index].index("--index") + 1
        ] == target.index
    assert "Textbook RAG target: http://runtime-es.test:9200/runtime-textbooks" in capsys.readouterr().out


def test_compose_uses_one_container_safe_textbook_target_for_backend_and_worker() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count(
        "TEXTBOOK_RAG_ELASTICSEARCH_URL: "
        "${TEXTBOOK_RAG_ELASTICSEARCH_URL:-http://elasticsearch:9200}"
    ) == 2
    assert compose.count(
        "TEXTBOOK_RAG_ELASTICSEARCH_INDEX: "
        "${TEXTBOOK_RAG_ELASTICSEARCH_INDEX:-canonical-rag-chunks-qwen-v1}"
    ) == 2
    assert "TEXTBOOK_RAG_ELASTICSEARCH_URL: http://127.0.0.1:9200" not in compose
    assert "${CHEMISTRY_RAG_HOST_ROOT:-./data}:/chemistry-rag/data:ro" in compose
    assert "E:/chemistry-rag:/chemistry-rag:ro" not in compose


def test_reprojection_preflight_rejects_an_unsupported_embedding_protocol() -> None:
    settings = Settings(
        data_backend="postgres",
        textbook_rag_elasticsearch_url="http://elasticsearch.test:9200",
        textbook_rag_elasticsearch_index="canonical-rag-chunks-qwen-v1",
        textbook_rag_embedding_base_url="https://embedding.example.test/v1",
        textbook_rag_embedding_api_key="secret",
        textbook_rag_embedding_model="bge-m3",
        textbook_rag_embedding_dimension=1024,
        textbook_rag_embedding_protocol="unsupported",
    )

    with pytest.raises(TextbookRecoveryError) as raised:
        validate_reprojection_configuration(settings)

    assert raised.value.reason == "online_textbook_reprojection_not_configured"
    assert "embedding_protocol_unsupported" in raised.value.details["missing"]


def test_online_ingestion_runbook_requires_migrations_before_backend_and_worker() -> None:
    runbook = Path("docs/online-textbook-ingestion.md").read_text(encoding="utf-8")
    migration = runbook.index("python scripts/apply_migrations.py")
    services = runbook.index(
        "docker compose up -d backend textbook-ingestion-worker web-teacher"
    )

    assert migration < services
    assert "backend 和 worker 启动时**不会**自动应用数据库迁移" in runbook
