import "@testing-library/jest-dom/vitest";
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AssistantMarkdownContent } from "./lib/assistant-markdown";

const rawCommandPatterns = [
  /\\ce\b/,
  /\\ch\b/,
  /\\mathrm\b/,
  /\\rightarrow\b/,
  /\\cdot\b/,
  /\\frac\b/,
  /\\sqrt\b/,
  /\\sum\b/,
  /\\leq\b/,
];

function visibleText() {
  const clone = document.body.cloneNode(true) as HTMLElement;
  clone.querySelectorAll("annotation, script, style").forEach((node) => node.remove());
  return clone.textContent || "";
}

function expectNoVisibleLatexLeaks() {
  const text = visibleText();
  rawCommandPatterns.forEach((pattern) => {
    expect(text).not.toMatch(pattern);
  });
  expect(document.querySelector(".katex-error")).toBeNull();
}

describe("AssistantMarkdownContent", () => {
  afterEach(() => cleanup());

  it("renders mhchem and unit formulas without visible raw commands", () => {
    render(
      <AssistantMarkdownContent
        text={String.raw`Reaction: $\ce{Cl2 + 2Br- -> 2Cl- + Br2}$ and $0.1\,\mathrm{mol\cdot L^{-1}}$.`}
      />,
    );

    expect(document.querySelectorAll(".assistant-katex .katex").length).toBeGreaterThan(0);
    expectNoVisibleLatexLeaks();
  });

  it("renders general inline and display math", () => {
    render(
      <AssistantMarkdownContent
        text={String.raw`Inline: $E=mc^2$, $x=\frac{-b+\sqrt{b^2-4ac}}{2a}$.

Display:

$$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$$`}
      />,
    );

    expect(document.querySelectorAll(".assistant-katex .katex").length).toBeGreaterThanOrEqual(3);
    expect(document.querySelector(".assistant-katex .katex .mfrac")).not.toBeNull();
    expect(document.querySelector(".assistant-katex .katex .sqrt")).not.toBeNull();
    expectNoVisibleLatexLeaks();
  });

  it("renders representative mhchem reaction forms", () => {
    render(
      <AssistantMarkdownContent
        text={String.raw`Common reactions:

- combustion: $\ce{2H2 + O2 -> 2H2O}$
- precipitation: $\ce{Ag+ + Cl- -> AgCl(s)}$
- equilibrium: $\ce{CO2 + H2O <=> HCO3- + H+}$
- redox half reaction: $\ce{MnO4^- + 8H+ + 5e- -> Mn^2+ + 4H2O}$
- gas and precipitate marks: $\ce{CaCO3 -> CaO + CO2 ^}$ and $\ce{Ba^2+ + SO4^2- -> BaSO4 v}$`}
      />,
    );

    expect(document.querySelectorAll(".assistant-katex .katex").length).toBeGreaterThanOrEqual(6);
    expect(document.querySelectorAll(".assistant-katex .katex .mrel").length).toBeGreaterThanOrEqual(5);
    expectNoVisibleLatexLeaks();
  });

  it("renders mixed chemistry explanations with mathematical notation", () => {
    render(
      <AssistantMarkdownContent
        text={String.raw`For the point $\ce{Cl2 + 2Br- -> 2Cl- + Br2}$, the oxidizing ability can be compared by standard potentials:

$$
\begin{aligned}
E^\circ(\ce{Cl2}/\ce{Cl-}) &= 1.36\,\mathrm{V}\\
E^\circ(\ce{Br2}/\ce{Br-}) &= 1.07\,\mathrm{V}\\
\Delta E^\circ &= 0.29\,\mathrm{V} > 0
\end{aligned}
$$

Therefore $\ce{Cl2}$ can oxidize $\ce{Br-}$ to $\ce{Br2}$.`}
      />,
    );

    expect(document.querySelectorAll(".assistant-katex .katex").length).toBeGreaterThanOrEqual(4);
    expect(document.querySelector(".assistant-katex .katex .mtable")).not.toBeNull();
    expectNoVisibleLatexLeaks();
  });

  it("wraps bare chemistry commands before rendering", () => {
    render(
      <AssistantMarkdownContent
        text={String.raw`设置「氯水 + KBr 溶液 + \ceCCl4」 反应方程式为：\ceCl2 + 2Br^- --> 2Cl^- + Br2。Reaction: \ce{Cl2 + 2Br- -> 2Cl- + Br2}. Unit: 0.1\,\mathrm{mol\cdot L^{-1}}. Alt: \ch{H2O}. Loose: \ceKMnO4, \ceMn^{2+}, \ceMnO2, \ceMnO4^{2-}. Equations: $\ceBr2 + 2I^- -- > 2Br^- + I2$.`}
      />,
    );

    expect(document.querySelectorAll(".assistant-katex .katex").length).toBeGreaterThan(0);
    expect(document.querySelector(".assistant-katex .katex .mrel")).not.toBeNull();
    expectNoVisibleLatexLeaks();
    expect(visibleText()).not.toMatch(/--\s*>|-->/);
    expect(visibleText()).toContain("反应方程式为");
  });

  it("normalizes screenshot-style assistant answers and evidence snippets", () => {
    render(
      <AssistantMarkdownContent
        text={String.raw`设置「氯水 + KBr 溶液 + \ceCCl4」这一实验点位，核心目的是验证卤素单质氧化性强弱顺序。

反应方程式为：
\ceCl2 + 2Br^- --> 2Cl^- + Br2

固定证据：0.1 mol\cdot$ L^{-1} KBr 溶液，\ceCCl4 层呈橙红色。`}
      />,
    );

    expect(document.querySelectorAll(".assistant-katex .katex").length).toBeGreaterThan(0);
    expectNoVisibleLatexLeaks();
    expect(visibleText()).not.toMatch(/--\s*>|\\ceCCl4|\\cdot/);
  });

  it("sanitizes invalid math fallback text", () => {
    render(<AssistantMarkdownContent text={String.raw`Bad math: $\mathrm{Cl_2$ then \rightarrow.`} />);

    expectNoVisibleLatexLeaks();
    expect(visibleText()).toContain("Cl_2");
  });
});
