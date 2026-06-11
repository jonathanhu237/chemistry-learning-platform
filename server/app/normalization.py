from __future__ import annotations

import re
from typing import Any

GENERAL_CHAPTER_ID = "CH00"
CHAPTER_IDS = [f"CH{number}" for number in range(13, 23)]
TEXTBOOK_CHAPTER_IDS = CHAPTER_IDS
ASSESSMENT_CHAPTER_IDS = TEXTBOOK_CHAPTER_IDS
CURRICULUM_CHAPTER_IDS = [*TEXTBOOK_CHAPTER_IDS, GENERAL_CHAPTER_ID]

CHAPTER_AREA_MAP: dict[str, dict[str, str]] = {
    "CH00": {"area_id": "general", "area_name": "通识", "chapter_title": "通识/跨章节"},
    "CH13": {"area_id": "p", "area_name": "p区", "chapter_title": "第 13 章 卤族元素"},
    "CH14": {"area_id": "p", "area_name": "p区", "chapter_title": "第 14 章 氧族元素"},
    "CH15": {"area_id": "p", "area_name": "p区", "chapter_title": "第 15 章 氮族元素"},
    "CH16": {"area_id": "p", "area_name": "p区", "chapter_title": "第 16 章 碳族元素"},
    "CH17": {"area_id": "p", "area_name": "p区", "chapter_title": "第 17 章 硼族元素"},
    "CH18": {"area_id": "s", "area_name": "s区", "chapter_title": "第 18 章 碱金属和碱土金属"},
    "CH19": {"area_id": "ds", "area_name": "ds区", "chapter_title": "第 19 章 铜锌副族元素"},
    "CH20": {"area_id": "d", "area_name": "d区", "chapter_title": "第 20 章 d区过渡金属元素"},
    "CH21": {"area_id": "f", "area_name": "f区", "chapter_title": "第 21 章 镧系和锕系元素"},
    "CH22": {"area_id": "integrated", "area_name": "综合", "chapter_title": "第 22 章 氢和稀有气体"},
}

AREA_DEFINITIONS: list[dict[str, Any]] = [
    {
        "area_id": "p",
        "area_name": "p区",
        "description": "主族 p 区元素性质、氧化还原与典型实验。",
        "chapter_ids": ["CH13", "CH14", "CH15", "CH16", "CH17"],
    },
    {
        "area_id": "s",
        "area_name": "s区",
        "description": "碱金属与碱土金属的递变规律、焰色反应和活泼性。",
        "chapter_ids": ["CH18"],
    },
    {
        "area_id": "ds",
        "area_name": "ds区",
        "description": "铜锌副族元素沉淀、配合物和氧化态转化。",
        "chapter_ids": ["CH19"],
    },
    {
        "area_id": "d",
        "area_name": "d区",
        "description": "过渡金属的颜色、氧化还原、配位和水解。",
        "chapter_ids": ["CH20"],
    },
    {
        "area_id": "f",
        "area_name": "f区",
        "description": "镧系与锕系元素的电子构型、收缩效应和分离规律。",
        "chapter_ids": ["CH21"],
    },
    {
        "area_id": "integrated",
        "area_name": "综合",
        "description": "氢、稀有气体等综合章节内容。",
        "chapter_ids": ["CH22"],
    },
    {
        "area_id": "general",
        "area_name": "通识",
        "description": "跨章节结构、氧化还原、周期性和平衡方法。",
        "chapter_ids": ["CH00"],
    },
]

LOW_QUALITY_QUESTION_TEXT = {
    "该说法与本章知识点无关。",
    "该知识点只适用于有机化学体系。",
    "该知识点不需要结合元素周期性或反应条件判断。",
}

EXPERIMENT_TITLE_CANDIDATES = [
    "卤素的氧化性",
    "卤素离子的还原性",
    "次氯酸盐的氧化性",
    "氯酸盐的氧化性",
    "氯含氧酸盐的氧化性",
    "卤化银的感光性",
    "过氧化氢的制备与性质",
    "过氧化氢的鉴定",
    "过氧化氢的氧化还原性",
    "二氧化硫的制备与性质",
    "SO3^2- 的检出",
    "硫代硫酸钠的性质",
    "过二硫酸盐的氧化性",
    "亚硝酸及其盐的性质",
    "硝酸及其盐的性质",
    "硝酸根的检验",
    "水中花园：难溶性硅酸盐的生成",
    "碱金属、碱土金属活泼性的比较",
    "焰色反应",
    "氢氧化物的性质",
    "氧化还原性",
    "ds区元素氢氧化物的生成与性质",
    "ds区元素配合物的生成与性质",
    "铜(I)化合物及其性质",
    "汞(II)和汞(I)相互转化",
    "d区元素氢氧化物的酸碱性",
    "过渡金属化合物的氧化还原性",
    "金属离子的水解作用",
    "过渡金属离子的颜色",
    "过渡金属离子的颜色变化",
    "金属离子配合物",
    "金属离子的鉴定",
]


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = text.replace("\u00a0", " ").replace("　", " ")
    return re.sub(r"\s+", " ", text).strip()


def text_preview(text: str, limit: int = 220) -> str:
    text = clean_text(text)
    return text[:limit] + ("..." if len(text) > limit else "")


def is_low_quality_experiment_name(name: str) -> bool:
    name = clean_text(name)
    if not name or len(name) > 35:
        return True
    bad_phrases = ["实验操作与现象", "实验现象", "待教师"]
    if any(phrase in name for phrase in bad_phrases):
        return True
    if len(name) > 18 and any(symbol in name for symbol in ["=", "→", "+"]):
        return True
    if re.match(r"^(取少量|向.+加入|以\s*0?\.?\d|分别?向|观察|滴加|加入)", name):
        return True
    if re.fullmatch(r"[\u4e00-\u9fffA-Za-z0-9·()（）+\-\s]{1,8}(溶液|试纸|水|酸|碱|盐)?", name):
        if any(term in name for term in ["溶液", "试纸", "氯水", "溴水", "碘水"]):
            return True
    return False


def equation_like(text: str) -> bool:
    text = clean_text(text)
    if not re.search(r"(→|=|⇌|<=>)", text):
        return False
    if len(text) < 6:
        return False
    return bool(re.search(r"[A-Z][a-z]?|[₂₃₄₅₆₇₈₉₀]|\d", text))


def infer_chapter_from_text(text: str) -> str | None:
    text = clean_text(text)
    keyword_map = [
        ("CH13", ["卤", "氯水", "KBr", "KI", "AgCl", "AgBr", "AgI"]),
        ("CH14", ["H2O2", "过氧化氢", "SO2", "SO3", "硫代硫酸", "过二硫酸"]),
        ("CH15", ["NH4", "NO3", "NO2", "硝酸", "亚硝酸", "磷酸", "砷", "锑", "铋"]),
        ("CH16", ["碳", "硅", "Sn", "Pb", "锡", "铅", "水中花园", "硅酸盐"]),
        ("CH17", ["硼", "铝", "Al", "硼酸"]),
        ("CH18", ["碱金属", "碱土金属", "焰色", "Li", "Na", "K", "Mg", "Ca"]),
        ("CH19", ["Cu", "Ag", "Zn", "Cd", "Hg", "铜", "银", "锌", "镉", "汞"]),
        ("CH20", ["Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "铬", "锰", "铁", "钴", "镍"]),
        ("CH21", ["镧", "锕", "稀土", "Ce", "La", "Ln"]),
        ("CH22", ["氢", "稀有气体", "氦", "氖", "氩", "Xe", "Kr"]),
    ]
    scores: dict[str, int] = {}
    for chapter_id, keywords in keyword_map:
        scores[chapter_id] = sum(1 for keyword in keywords if keyword in text)
    best = max(scores.items(), key=lambda item: item[1])
    return best[0] if best[1] else None
