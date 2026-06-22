import type { CSSProperties } from "react";
import type { StudentLearningArea, StudentLearningElementBadge, StudentLearningProfileSummary } from "../../api";
import { periodicElements } from "../../periodic";

export type AreaId = "hydrogen" | "p" | "s" | "ds" | "d" | "f";
type PeriodicArea = "s区" | "p区" | "d区" | "ds区" | "f区";

const areaIdByPeriodicArea: Record<PeriodicArea, AreaId> = {
  "s区": "s",
  "p区": "p",
  "d区": "d",
  "ds区": "ds",
  "f区": "f",
};

export const periodicAreaByAreaId: Record<AreaId, string> = {
  hydrogen: "氢元素",
  p: "p区",
  s: "s区",
  ds: "ds区",
  d: "d区",
  f: "f区",
};

export const periodicLegendLabelByAreaId: Record<AreaId, string> = {
  hydrogen: "氢元素",
  p: "p区元素",
  s: "s区元素",
  ds: "ds区元素",
  d: "d区元素",
  f: "f区元素",
};

export const periodicAreaOrder: AreaId[] = ["hydrogen", "p", "s", "ds", "d", "f"];
export const periodicPeriodLabels = ["一", "二", "三", "四", "五", "六", "七", "镧系", "锕系"];
const nobleGasSymbols = new Set(["He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"]);
export type PeriodicElementMeta = (typeof periodicElements)[number];

export function periodicAreaIdForElement(element: PeriodicElementMeta): AreaId {
  if (element.symbol === "H") return "hydrogen";
  if (nobleGasSymbols.has(element.symbol)) return "p";
  return areaIdByPeriodicArea[element.area as PeriodicArea];
}

export function periodicGridColumnForElement(element: PeriodicElementMeta): number {
  const displayGroup = element.area === "f区" && element.period >= 8 ? element.group - 1 : element.group;
  return displayGroup + 1;
}

export function periodicGridRowForPeriod(period: number): number {
  return period >= 8 ? period + 2 : period + 1;
}

export const areaSwatches: Record<AreaId, string> = {
  hydrogen: "#6f9f2e",
  p: "#0f8f72",
  s: "#9a6a11",
  ds: "#c89a2d",
  d: "#9e2f3d",
  f: "#8d4f9f",
};

export const areaInk: Record<AreaId, string> = {
  hydrogen: "#254509",
  p: "#063f31",
  s: "#46310a",
  ds: "#523a0c",
  d: "#4e1018",
  f: "#42204d",
};

const profileAreasByChapterId: Record<string, AreaId[]> = {
  CH13: ["p"],
  CH14: ["p"],
  CH15: ["p"],
  CH16: ["p"],
  CH17: ["p"],
  CH18: ["s"],
  CH19: ["ds"],
  CH20: ["d"],
  CH21: ["f"],
  CH22: ["hydrogen", "p"],
};

const elementEnglishNames: Record<string, string> = {
  H: "Hydrogen",
  He: "Helium",
  Li: "Lithium",
  B: "Boron",
  C: "Carbon",
  N: "Nitrogen",
  O: "Oxygen",
  F: "Fluorine",
  Ne: "Neon",
  Na: "Sodium",
  Mg: "Magnesium",
  Al: "Aluminium",
  Si: "Silicon",
  P: "Phosphorus",
  S: "Sulfur",
  Cl: "Chlorine",
  Ar: "Argon",
  K: "Potassium",
  Ca: "Calcium",
  Ti: "Titanium",
  V: "Vanadium",
  Cr: "Chromium",
  Mn: "Manganese",
  Fe: "Iron",
  Co: "Cobalt",
  Ni: "Nickel",
  Cu: "Copper",
  Zn: "Zinc",
  Ga: "Gallium",
  As: "Arsenic",
  Se: "Selenium",
  Br: "Bromine",
  Kr: "Krypton",
  Ag: "Silver",
  Cd: "Cadmium",
  In: "Indium",
  Sn: "Tin",
  Sb: "Antimony",
  Te: "Tellurium",
  I: "Iodine",
  Xe: "Xenon",
  At: "Astatine",
  Ba: "Barium",
  Hg: "Mercury",
  Tl: "Thallium",
  Pb: "Lead",
  Bi: "Bismuth",
};

export function periodicMetaForElement(symbol: string) {
  return periodicElements.find((element) => element.symbol === symbol) || null;
}

export function elementEnglishName(element: StudentLearningElementBadge): string {
  return elementEnglishNames[element.symbol] || element.symbol;
}

export function elementTileStyle(element: StudentLearningElementBadge): CSSProperties | undefined {
  const periodicElement = periodicMetaForElement(element.symbol);
  const areaId = periodicElement ? periodicAreaIdForElement(periodicElement) : null;
  if (!areaId) return undefined;
  return {
    "--element-area-color": areaSwatches[areaId],
    "--element-area-ink": areaInk[areaId],
  } as CSSProperties;
}

export function normalizeAreaId(value: string | null | undefined): AreaId | null {
  if (value === "hydrogen" || value === "p" || value === "s" || value === "d" || value === "ds" || value === "f") return value;
  return null;
}

export function firstEnabledArea(areas: StudentLearningArea[]): AreaId | null {
  const match = areas.find((area) => area.enabled && normalizeAreaId(area.area_id));
  return normalizeAreaId(match?.area_id);
}

export function profileAreaIds(profile: StudentLearningProfileSummary): AreaId[] {
  const mappedAreas = profileAreasByChapterId[profile.chapter_id];
  if (mappedAreas) return mappedAreas;

  const text = `${profile.title} ${profile.subtitle} ${profile.family_name}`;
  if (text.includes("氢")) return ["hydrogen"];
  if (text.includes("ds")) return ["ds"];
  if (text.includes("s区")) return ["s"];
  if (text.includes("p区")) return ["p"];
  if (text.includes("d区")) return ["d"];
  if (text.includes("f区")) return ["f"];
  return [];
}

export function profileAreaId(profile: StudentLearningProfileSummary): AreaId | null {
  return profileAreaIds(profile)[0] || null;
}
