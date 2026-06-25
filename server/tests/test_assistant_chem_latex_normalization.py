from __future__ import annotations

from server.app.domains.assistant.output_normalization import normalize_assistant_formula_output as _normalize_assistant_formula_output


def test_normalizes_bare_chemistry_commands():
    answer = r"Reaction: \ce{Cl2 + 2Br- -> 2Cl- + Br2}. Unit: 0.1\,\mathrm{mol\cdot L^{-1}}."

    normalized = _normalize_assistant_formula_output(answer)

    assert r"$\ce{Cl2 + 2Br- -> 2Cl- + Br2}$" in normalized
    assert r"$0.1\,\mathrm{mol\cdot L^{-1}}$" in normalized


def test_normalizes_loose_chemistry_commands():
    answer = r"高锰酸钾（\ceKMnO4）会被还原为 \ceMn^{2+}、\ceMnO2 或 \ceMnO4^{2-}。"

    normalized = _normalize_assistant_formula_output(answer)

    assert r"$\ce{KMnO4}$" in normalized
    assert r"$\ce{Mn^{2+}}$" in normalized
    assert r"$\ce{MnO2}$" in normalized
    assert r"$\ce{MnO4^{2-}}$" in normalized
    assert r"\ceK" not in normalized


def test_normalizes_loose_reaction_equations():
    answer = r"原理：\ceCl2 + 2Br^- --> 2Cl^- + Br2；对比：$\ceBr2 + 2I^- -- > 2Br^- + I2$。"

    normalized = _normalize_assistant_formula_output(answer)

    assert r"$\ce{Cl2 + 2Br^- -> 2Cl^- + Br2}$" in normalized
    assert r"$\ce{Br2 + 2I^- -> 2Br^- + I2}$" in normalized
    assert "-->" not in normalized
    assert "-- >" not in normalized
    assert r"\ceCl" not in normalized


def test_loose_reaction_does_not_swallow_surrounding_chinese_text():
    answer = r"设置「氯水 + KBr 溶液 + \ceCCl4」 反应方程式为：\ceCl2 + 2Br^- --> 2Cl^- + Br2。"

    normalized = _normalize_assistant_formula_output(answer)

    assert r"$\ce{CCl4}$" in normalized
    assert r"$\ce{Cl2 + 2Br^- -> 2Cl^- + Br2}$" in normalized
    assert "反应方程式为" in normalized
    assert "CCl4」 反应" not in normalized


def test_normalizes_alternate_math_delimiters():
    answer = r"Use \(\mathrm{Cl_2}\) and \[\ce{Cl2 + 2Br- -> 2Cl- + Br2}\]."

    normalized = _normalize_assistant_formula_output(answer)

    assert r"$\mathrm{Cl_2}$" in normalized
    assert r"$$\ce{Cl2 + 2Br- -> 2Cl- + Br2}$$" in normalized
    assert r"\(" not in normalized
    assert r"\[" not in normalized


def test_preserves_fenced_code_blocks():
    answer = r"""Before \mathrm{Cl_2}
```latex
\mathrm{DoNotWrap}
```
After \rightarrow"""

    normalized = _normalize_assistant_formula_output(answer)

    assert r"Before $\mathrm{Cl_2}$" in normalized
    assert "```latex\n\\mathrm{DoNotWrap}\n```" in normalized
    assert r"After $\rightarrow$" in normalized
