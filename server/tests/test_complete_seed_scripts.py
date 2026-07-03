from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import scripts.seed_demo_identities as identity_seed
import scripts.seed_experiment_videos as video_seed


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_demo_identity_seed_payload_has_expected_demo_roster() -> None:
    payload = identity_seed.load_seed()

    result = identity_seed.validate_seed_payload(payload)

    assert result["ok"] is True
    assert result["summary"] == {"teacher": 1, "classes": 1, "students": 30}
    assert payload["teacher"]["username"] == "teacher"
    assert payload["class"]["id"] == "seed-class-2026"
    assert payload["class"]["class_name"] == "26级本科 1 班"
    assert {student["student_id"] for student in payload["students"]} == {str(26320000 + index) for index in range(1, 31)}
    assert payload["students"][0]["student_name"] == "张三"
    assert payload["students"][1]["student_name"] == "李四"


def test_video_seed_payload_covers_all_points_with_one_binding_per_canonical_point() -> None:
    payload = video_seed.load_manifest()

    result = video_seed.validate_manifest_payload(payload)
    coverage_keys = [
        binding.get("canonical_point_id") or binding["node_id"]
        for binding in payload["bindings"]
    ]

    assert result["ok"] is True
    assert payload["expected_counts"]["active_catalog_point_nodes"] == 393
    assert len(payload["bindings"]) == len(set(coverage_keys)) == 357
    assert payload["expected_counts"]["placeholder_video_covered_point_nodes"] == 388
    assert {asset["kind"] for asset in payload["assets"]} == {"real_video", "placeholder_video"}


def test_video_seed_payload_rejects_duplicate_canonical_coverage() -> None:
    payload = video_seed.load_manifest()
    duplicate = dict(payload["bindings"][0])
    duplicate["id"] = "11111111-1111-1111-1111-111111111111"
    payload["bindings"] = [*payload["bindings"], duplicate]

    result = video_seed.validate_manifest_payload(payload)

    assert result["ok"] is False
    assert any("duplicates coverage key" in error for error in result["errors"])


def test_video_seed_media_destination_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsafe media relative path"):
        video_seed._safe_media_destination(tmp_path, "../outside.mp4")


def test_video_seed_file_restore_verifies_and_copies_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_root = tmp_path / "repo"
    source = fake_root / "data" / "seed" / "media" / "fixture" / "source.mp4"
    source.parent.mkdir(parents=True)
    content = b"fake-mp4-content"
    source.write_bytes(content)
    monkeypatch.setattr(video_seed, "ROOT", fake_root)
    payload = {
        "assets": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "seed_source_path": "data/seed/media/fixture/source.mp4",
                "target_relative_path": "seed/fixture/source.mp4",
                "file_size_bytes": len(content),
                "checksum_sha256": _sha256(content),
            }
        ]
    }
    media_root = tmp_path / "media"

    report = video_seed._restore_files(payload, media_root)

    assert report["restored"] == 1
    assert (media_root / "seed" / "fixture" / "source.mp4").read_bytes() == content


def test_video_seed_file_restore_rejects_corrupt_fixture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_root = tmp_path / "repo"
    source = fake_root / "data" / "seed" / "media" / "fixture" / "source.mp4"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"actual")
    monkeypatch.setattr(video_seed, "ROOT", fake_root)
    payload = {
        "assets": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "seed_source_path": "data/seed/media/fixture/source.mp4",
                "target_relative_path": "seed/fixture/source.mp4",
                "file_size_bytes": len(b"actual"),
                "checksum_sha256": _sha256(b"expected"),
            }
        ]
    }

    with pytest.raises(ValueError, match="Seed source checksum mismatch"):
        video_seed._restore_files(payload, tmp_path / "media")
