from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from server.app.auth import AuthUser
from server.app.domains.student_learning import point_detail as learning_service
from server.app.domains.student_learning.point_detail import (
    _areas_for_groups,
    _build_parent_groups,
    _choose_recommendation,
    _latest_pretest_area_id,
    _lowest_mastery_chapter_id,
    _record_learning_event,
    validate_student_learning_experiment_coverage,
    validate_student_learning_profiles,
)
from server.app.normalization import AREA_DEFINITIONS, CHAPTER_AREA_CONTEXTS, CHAPTER_AREA_MAP
from server.tests.route_helpers import assert_route

ROOT = Path(__file__).resolve().parents[2]


def _experiment(
    experiment_id: str,
    *,
    code: str,
    title: str,
    parent_code: str,
    parent_title: str,
    chapter_id: str,
    display_order: int,
    questions: int = 0,
) -> dict[str, object]:
    return {
        "id": experiment_id,
        "code": code,
        "title": title,
        "summary": f"{title} summary",
        "status": "published",
        "display_order": display_order,
        "metadata": {
            "parent_code": parent_code,
            "parent_title": parent_title,
            "module_display_title": "Module",
            "video_candidates": ["Candidate video"],
        },
        "chapter_bindings": [{"chapter_id": chapter_id, "coverage_type": "primary", "sort_order": 1}],
        "media_resources": [],
        "published_question_count": questions,
    }


class _FailingSession:
    def __init__(self) -> None:
        self.rolled_back = False

    def execute(self, *_args, **_kwargs):
        raise SQLAlchemyError("missing optional student learning table")

    def rollback(self) -> None:
        self.rolled_back = True


def test_student_learning_routes_are_registered() -> None:
    assert_route("/api/student/learning-home", "GET")
    assert_route("/api/student/learning-page", "GET")
    assert_route("/api/student/chapters/{chapter_id}/catalog", "GET")
    assert_route("/api/student/catalog/nodes/{node_id}", "GET")
    assert_route("/api/student/catalog/points/{node_id}", "GET")


def test_periodic_area_definitions_use_new_learning_taxonomy() -> None:
    area_ids = [area["area_id"] for area in AREA_DEFINITIONS]

    assert area_ids[:6] == ["hydrogen", "p", "s", "ds", "d", "f"]
    assert "integrated" not in area_ids
    assert CHAPTER_AREA_MAP["CH22"]["area_id"] == "hydrogen"
    assert CHAPTER_AREA_CONTEXTS["CH22"] == ("hydrogen", "p")


def test_student_learning_profile_seed_is_valid() -> None:
    result = validate_student_learning_profiles()

    assert result["ok"] is True
    assert result["profile_count"] == 10
    assert result["enabled_profile_count"] == 10


def test_student_learning_profile_seed_has_element_card_copy() -> None:
    result = validate_student_learning_profiles()

    assert result["ok"] is True
    assert not [error for error in result["errors"] if "missing card copy" in error]


def test_hydrogen_noble_gas_profile_covers_complete_18th_group() -> None:
    seed = learning_service._student_learning_seed()
    profile = next(profile for profile in seed["profiles"] if profile["chapter_id"] == "CH22")

    assert profile["element_symbols"] == ["H", "He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"]
    assert [element["symbol"] for element in profile["elements"]] == profile["element_symbols"]


def test_student_learning_profile_validation_reports_missing_element_card_copy(monkeypatch) -> None:
    profile = {
        "profile_id": "test-profile",
        "chapter_id": "CH_TEST",
        "title": "Test profile",
        "hero": {"title": "Test"},
        "property_cards": [
            {"key": "atomic_number", "label": "Atomic number", "value": "1"},
            {"key": "electron_configuration", "label": "Electron configuration", "value": "1s1"},
            {"key": "group", "label": "Group", "value": "1"},
            {"key": "common_valence", "label": "Common valence", "value": "+1"},
            {"key": "elemental_state", "label": "State", "value": "Gas"},
            {"key": "redox", "label": "Redox", "value": "Reducing"},
        ],
        "family_common_properties": [{"key": "group", "label": "Group", "value": "1"}],
        "property_sections": [{"key": "section", "title": "Section"}],
        "elements": [
            {
                "symbol": "H",
                "name": "Hydrogen",
                "atomic_number": 1,
                "electron_configuration": "1s1",
                "group_label": "1",
                "common_valence": "+1",
                "state": "Gas",
                "redox_tendency": "Reducing",
                "relative_atomic_mass": "1.008",
                "group": "1",
                "period": 1,
                "block": "s",
                "state_at_20c": "Gas",
                "density": "0.000082 g/cm3",
                "rsc_url": "https://periodic-table.rsc.org/element/1/hydrogen",
                "fact_source": "Royal Society of Chemistry Periodic Table",
            }
        ],
    }
    monkeypatch.setattr(learning_service, "_student_learning_seed", lambda: {"version": "test", "profiles": [profile]})

    result = validate_student_learning_profiles()

    assert result["ok"] is False
    assert any("test-profile: element H missing card copy card_focus, card_relevance, card_tags" in error for error in result["errors"])


def test_element_badges_expose_card_copy_and_preserve_detail_fields() -> None:
    profile = {
        "elements": [
            {
                "symbol": "Cl",
                "name": "Chlorine",
                "atomic_number": 17,
                "card_focus": "Strong oxidizer",
                "card_relevance": "Oxidizes bromide and iodide ions.",
                "card_tags": ["halogen", "oxidizer"],
                "electron_configuration": "[Ne]3s2 3p5",
                "common_valence": "-1, 0, +1, +3, +5, +7",
                "redox_tendency": "Cl2 can oxidize Br- and I-.",
                "note": "Detailed note stays available.",
            }
        ]
    }

    badge = learning_service._element_badges(profile)[0]

    assert badge.card_focus == "Strong oxidizer"
    assert badge.card_relevance == "Oxidizes bromide and iodide ions."
    assert badge.card_tags == ["halogen", "oxidizer"]
    assert badge.redox_tendency == "Cl2 can oxidize Br- and I-."
    assert badge.note == "Detailed note stays available."


def test_element_badges_allow_missing_card_copy_during_mapping_migration() -> None:
    badge = learning_service._element_badges({"elements": [{"symbol": "H", "name": "Hydrogen"}]})[0]

    assert badge.card_focus is None
    assert badge.card_relevance is None
    assert badge.card_tags == []


def test_student_learning_experiment_coverage_requires_every_profile_chapter() -> None:
    chapters = ["CH13", "CH14", "CH15", "CH16", "CH17", "CH18", "CH19", "CH20", "CH21", "CH22"]
    experiments = [
        _experiment(
            f"EXP_{chapter_id}",
            code=f"{index + 1}-1",
            title=f"{chapter_id} experiment",
            parent_code=f"{index + 1}-1",
            parent_title=f"{chapter_id} parent",
            chapter_id=chapter_id,
            display_order=index + 1,
        )
        for index, chapter_id in enumerate(chapters)
    ]

    result = validate_student_learning_experiment_coverage(experiments)

    assert result["ok"] is True
    assert result["covered_experiment_count"] == len(chapters)
    assert result["uncovered_experiment_count"] == 0
    assert result["profiles_without_experiments"] == []


def test_student_learning_experiment_coverage_rejects_unmapped_published_experiments() -> None:
    chapters = ["CH13", "CH14", "CH15", "CH16", "CH17", "CH18", "CH19", "CH20", "CH21", "CH22"]
    experiments = [
        _experiment(
            f"EXP_{chapter_id}",
            code=f"{index + 1}-1",
            title=f"{chapter_id} experiment",
            parent_code=f"{index + 1}-1",
            parent_title=f"{chapter_id} parent",
            chapter_id=chapter_id,
            display_order=index + 1,
        )
        for index, chapter_id in enumerate(chapters)
    ]
    experiments.append(
        _experiment(
            "EXP_UNMAPPED",
            code="99-1",
            title="Unmapped experiment",
            parent_code="99-1",
            parent_title="Unmapped parent",
            chapter_id="CH99",
            display_order=99,
        )
    )

    result = validate_student_learning_experiment_coverage(experiments)

    assert result["ok"] is False
    assert result["uncovered_experiment_count"] == 1
    assert any("EXP_UNMAPPED" in error for error in result["errors"])


def test_student_learning_seed_covers_all_formal_experiments() -> None:
    data = json.loads((ROOT / "data" / "seed" / "formal_experiments.json").read_text(encoding="utf-8-sig"))
    experiments = [
        experiment
        for experiment in data.get("experiments") or []
        if isinstance(experiment, dict) and str(experiment.get("status") or "published") == "published"
    ]

    result = validate_student_learning_experiment_coverage(experiments)

    assert result["ok"] is True
    assert result["published_experiment_count"] == 77
    assert result["covered_experiment_count"] == 77
    assert result["uncovered_experiment_count"] == 0
    assert result["profiles_without_experiments"] == []


def test_student_learning_recommendation_tables_are_optional() -> None:
    pretest_session = _FailingSession()
    mastery_session = _FailingSession()

    assert _latest_pretest_area_id(pretest_session, "20240001") is None
    assert pretest_session.rolled_back is True
    assert _lowest_mastery_chapter_id(mastery_session, student_id="20240001", area_id="p") is None
    assert mastery_session.rolled_back is True


def test_student_learning_event_recording_is_best_effort() -> None:
    session = _FailingSession()
    user = AuthUser(
        id="00000000-0000-0000-0000-000000000000",
        username="20240001",
        role="student",
        display_name="Student",
        status="active",
        must_change_password=False,
        student_id="20240001",
    )

    _record_learning_event(session, user=user, event_type="learning_profile_opened", chapter_id="CH13")

    assert session.rolled_back is True


def test_parent_groups_follow_experiment_parent_titles_and_include_f_area() -> None:
    groups = _build_parent_groups(
        [
            _experiment(
                "EXP_19_1_01",
                code="19-1-01",
                title="Halogen displacement",
                parent_code="19-1",
                parent_title="Experiment 19-1 Halogens",
                chapter_id="CH13",
                display_order=1,
                questions=4,
            ),
            _experiment(
                "EXP_20_2_01",
                code="20-2-01",
                title="Transition metal properties",
                parent_code="20-2",
                parent_title="Experiment 20-2 d-block ions",
                chapter_id="CH20",
                display_order=20,
                questions=2,
            ),
            _experiment(
                "EXP_21_1_01",
                code="21-1-01",
                title="Lanthanide properties",
                parent_code="21-1",
                parent_title="Experiment 21-1 Lanthanides",
                chapter_id="CH21",
                display_order=99,
            ),
        ]
    )

    assert [group.parent_code for group in groups] == ["19-1", "20-2", "21-1"]
    assert groups[0].area_id == "p"
    assert groups[0].parent_title == "Experiment 19-1 Halogens"

    areas = {area.area_id: area for area in _areas_for_groups(groups)}
    assert areas["f"].enabled is True
    assert areas["p"].question_count == 4


def test_student_learning_area_taxonomy_exposes_hydrogen_and_ch22_p_context() -> None:
    groups = _build_parent_groups(
        [
            _experiment(
                "EXP_22_1_01",
                code="22-1-01",
                title="Hydrogen and noble gas properties",
                parent_code="22-1",
                parent_title="Experiment 22-1 Hydrogen and noble gases",
                chapter_id="CH22",
                display_order=22,
            ),
        ]
    )

    assert [(group.area_id, group.parent_code) for group in groups] == [
        ("hydrogen", "22-1"),
        ("p", "22-1"),
    ]
    assert [area.area_id for area in _areas_for_groups(groups)] == ["hydrogen", "p", "s", "ds", "d", "f"]


def test_recommendation_falls_back_when_pretest_area_has_no_experiments() -> None:
    groups = _build_parent_groups(
        [
            _experiment(
                "EXP_19_1_01",
                code="19-1-01",
                title="Halogen displacement",
                parent_code="19-1",
                parent_title="Experiment 19-1 Halogens",
                chapter_id="CH13",
                display_order=1,
            ),
            _experiment(
                "EXP_18_1_01",
                code="19-6-01",
                title="Flame test",
                parent_code="19-6",
                parent_title="Experiment 19-6 Metal ions",
                chapter_id="CH18",
                display_order=18,
            ),
        ]
    )

    assert _choose_recommendation(groups=groups, pretest_area_id="f", mastery_chapter_id=None) == ("p", "19-1")
    assert _choose_recommendation(groups=groups, pretest_area_id="s", mastery_chapter_id="CH18") == ("s", "19-6")
