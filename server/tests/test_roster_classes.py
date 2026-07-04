from __future__ import annotations

from server.app.domains.roster.classes import _natural_class_sort_key


def test_class_sort_key_orders_demo_class_names_naturally() -> None:
    rows = [
        {"id": "class-10", "class_name": "26 级本科 10 班"},
        {"id": "class-2", "class_name": "26 级本科 2 班"},
        {"id": "class-1", "class_name": "26 级本科 1 班"},
    ]

    assert [row["class_name"] for row in sorted(rows, key=_natural_class_sort_key)] == [
        "26 级本科 1 班",
        "26 级本科 2 班",
        "26 级本科 10 班",
    ]
