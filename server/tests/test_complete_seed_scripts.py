from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import scripts.seed_demo_student_assessments as assessment_seed
import scripts.seed_demo_identities as identity_seed
import scripts.seed_experiment_videos as video_seed


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_demo_identity_seed_payload_has_expected_demo_roster() -> None:
    payload = identity_seed.load_seed()

    result = identity_seed.validate_seed_payload(payload)

    assert result["ok"] is True
    assert result["summary"] == {"teacher": 1, "classes": 5, "students": 150}
    assert payload["teacher"]["username"] == "teacher"
    assert payload["class"]["id"] == "seed-class-2026"
    assert payload["class"]["class_name"] == "26 级本科 1 班"
    assert [klass["class_name"] for klass in payload["classes"]] == [f"26 级本科 {index} 班" for index in range(1, 6)]
    assert {student["student_id"] for student in payload["students"]} == {
        f"2632{class_index:02d}{student_index:02d}"
        for class_index in range(5)
        for student_index in range(1, 31)
    }
    assert {student["class_id"] for student in payload["students"]} == {
        "seed-class-2026",
        "seed-class-2026-2",
        "seed-class-2026-3",
        "seed-class-2026-4",
        "seed-class-2026-5",
    }
    assert payload["students"][0]["student_name"] == "张三"
    assert payload["students"][1]["student_name"] == "李四"


def test_demo_assessment_seed_builds_varied_student_score_targets() -> None:
    payload = identity_seed.load_seed()
    students = assessment_seed.seed_students(payload)

    ratios = [assessment_seed.target_correct_ratio(student) for student in students]

    assert len(students) == 150
    assert min(ratios) < 0.45
    assert max(ratios) > 0.85
    assert len({round(ratio, 3) for ratio in ratios}) > 20


def test_demo_assessment_seed_gives_zhangsan_distinct_mastery_profile() -> None:
    targets = assessment_seed.SHOWCASE_CHAPTER_MASTERY_TARGETS
    sample_scores = [
        assessment_seed.showcase_mastery_score(chapter_id, f"{chapter_id}-point-{index}")
        for index, chapter_id in enumerate(targets)
    ]

    assert assessment_seed.SHOWCASE_STUDENT_ID == "26320001"
    assert min(sample_scores) < 35
    assert max(sample_scores) > 85
    assert all(abs(score - 50) >= 5 for score in sample_scores)


def test_demo_assessment_seed_generates_wrong_answers_by_question_type() -> None:
    single_choice = type(
        "Question",
        (),
        {
            "id": "q1",
            "question_type": "single_choice",
            "options": [{"label": "A", "value": "A"}, {"label": "B", "value": "B"}],
            "answer": {"value": "A"},
        },
    )()
    true_false = type(
        "Question",
        (),
        {
            "id": "q2",
            "question_type": "true_false",
            "options": [],
            "answer": {"value": True},
        },
    )()
    fill_blank = type(
        "Question",
        (),
        {
            "id": "q3",
            "question_type": "fill_blank",
            "options": [],
            "answer": {"accepted_answers": ["正确答案"]},
        },
    )()

    assert assessment_seed.correct_answer(fill_blank) == "正确答案"
    assert assessment_seed.wrong_answer(single_choice) == "B"
    assert assessment_seed.wrong_answer(true_false) is False
    assert assessment_seed.wrong_answer(fill_blank) == "模拟错误答案"


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
