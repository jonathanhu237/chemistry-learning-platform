import { describe, expect, it } from "vitest";
import type { StudentLearningElementBadge, StudentLearningProfile } from "../../api";
import { deriveElectronShells, learningElementToAtomModel } from "./learningAtomAdapter";

const profile = {
  profile_id: "halogens-17",
  chapter_id: "CH17",
  title: "17族（卤素）",
  family_name: "卤素",
} as StudentLearningProfile;

function element(overrides: Partial<StudentLearningElementBadge>): StudentLearningElementBadge {
  return {
    symbol: "Cl",
    name: "氯",
    atomic_number: 17,
    electron_configuration: "[Ne]3s2 3p5",
    common_valence: "-1, +1, +3, +5, +7",
    relative_atomic_mass: "35.45",
    group: "17",
    period: 3,
    block: "p",
    state_at_20c: "Gas",
    density: "0.002898 g/cm3",
    rsc_url: "https://periodic-table.rsc.org/element/17/chlorine",
    fact_source: "Royal Society of Chemistry Periodic Table",
    ...overrides,
  };
}

describe("learning atom adapter", () => {
  it("expands noble-gas shorthand into electron shells", () => {
    expect(deriveElectronShells("[Ne]3s2 3p5", 17)).toEqual([2, 8, 7]);
    expect(deriveElectronShells("[Ar]3d10 4s2 4p5", 35)).toEqual([2, 8, 18, 7]);
  });

  it("handles explicit d configurations and spaced RSC-style exponents", () => {
    expect(deriveElectronShells("[Ar] 3d 5 4s 1", 24)).toEqual([2, 8, 13, 1]);
    expect(deriveElectronShells("[Ar]3d6 4s2", 26)).toEqual([2, 8, 14, 2]);
  });

  it("falls back from atomic number and reports missing model fields", () => {
    expect(deriveElectronShells("", 17)).toEqual([2, 8, 7]);
    const model = learningElementToAtomModel(element({ electron_configuration: "" }), profile);
    expect(model.shells).toEqual([2, 8, 7]);
    expect(model.unavailableReason).toContain("电子排布");
  });

  it("maps RSC physical facts and teaching fields without mixing them", () => {
    const model = learningElementToAtomModel(element({ redox_tendency: "X₂ 氧化性递减" }), profile);
    expect(model.relativeAtomicMass).toBe("35.45");
    expect(model.stateAt20C).toBe("气体");
    expect(model.oxidationStates).toBe("-1, +1, +3, +5, +7");
    expect(model.redoxTendency).toBe("X₂ 氧化性递减");
    expect(model.sourceUrl).toBe("https://periodic-table.rsc.org/element/17/chlorine");
  });

  it("shows unknown RSC density without appending a fake unit", () => {
    const model = learningElementToAtomModel(element({ density: "Unknown g/cm3" }), profile);
    expect(model.density).toBe("未知");
  });
});
