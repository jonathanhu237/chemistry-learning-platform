import { describe, expect, it } from "vitest";
import type { AtomViewerElement } from "./atomTypes";
import { getOrbitalChoiceOptions, parseValenceSubshells, resolveOrbitalChoice } from "./orbitalOptions";

const baseElement: AtomViewerElement = {
  atomicNumber: 83,
  symbol: "Bi",
  name: "Bismuth",
  englishName: "Bismuth",
  category: "pnictogen",
  group: "15",
  period: 6,
  block: "p",
  stateAt20C: "Solid",
  density: "9.79 g/cm3",
  oxidationStates: "+3, +5",
  relativeAtomicMass: "208.980",
  electronConfiguration: "[Xe]4f14 5d10 6s2 6p3",
  shells: [2, 8, 18, 32, 18, 5],
  accent: "#0f7b4d",
  sourceUrl: null,
  sourceLabel: "",
  teachingNote: "",
  redoxTendency: "",
};

describe("orbital options", () => {
  it("keeps every post-core subshell in configuration order", () => {
    expect(parseValenceSubshells(baseElement).map((subshell) => subshell.id)).toEqual(["4f", "5d", "6s", "6p"]);

    const allSubshellOptions = getOrbitalChoiceOptions(baseElement)
      .filter((option) => !option.isAuto && option.variant === "all")
      .map((option) => option.id);

    expect(allSubshellOptions).toEqual(["4f:all", "5d:all", "6s:all", "6p:all"]);
  });

  it("uses the characteristic open p subshell as the default choice", () => {
    const autoChoice = resolveOrbitalChoice(baseElement, "auto");

    expect(autoChoice.subshell.id).toBe("6p");
    expect(autoChoice.label).toBe("6p3 all");
  });
});
