import type { CSSProperties } from "react";
import type { StudentLearningArea, StudentLearningElementBadge, StudentLearningProfileSummary } from "../../api";
import { periodicElements } from "../../periodic";

export type AreaId = "p" | "s" | "ds" | "d" | "f" | "integrated";
type PeriodicArea = "s区" | "p区" | "d区" | "ds区" | "f区";

const areaIdByPeriodicArea: Record<PeriodicArea, AreaId> = {
  "s区": "s",
  "p区": "p",
  "d区": "d",
  "ds区": "ds",
  "f区": "f",
};

export const periodicAreaByAreaId: Record<AreaId, string> = {
  p: "p区",
  s: "s区",
  ds: "ds区",
  d: "d区",
  f: "f区",
  integrated: "氢和稀有气体",
};

export const periodicLegendLabelByAreaId: Record<AreaId, string> = {
  p: "p区元素",
  s: "s区元素",
  ds: "ds区元素",
  d: "d区元素",
  f: "f区元素",
  integrated: "氢和稀有气体",
};

export const periodicAreaOrder: AreaId[] = ["p", "s", "ds", "d", "f", "integrated"];
export const periodicPeriodLabels = ["一", "二", "三", "四", "五", "六", "七", "镧系", "锕系"];
const integratedElementSymbols = new Set(["H", "He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"]);
export type PeriodicElementMeta = (typeof periodicElements)[number];

export function periodicAreaIdForElement(element: PeriodicElementMeta): AreaId {
  if (integratedElementSymbols.has(element.symbol)) return "integrated";
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
  p: "#2f9d70",
  s: "#8cc95f",
  ds: "#d7ab3c",
  d: "#6fa3d8",
  f: "#a77bd2",
  integrated: "#86b4d2",
};

export const areaInk: Record<AreaId, string> = {
  p: "#0f3d2b",
  s: "#28430e",
  ds: "#4d3510",
  d: "#123556",
  f: "#3a2452",
  integrated: "#205071",
};

const profileAreaByChapterId: Record<string, AreaId> = {
  CH13: "p",
  CH14: "p",
  CH15: "p",
  CH16: "p",
  CH17: "p",
  CH18: "s",
  CH19: "ds",
  CH20: "d",
  CH21: "f",
  CH22: "integrated",
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
  if (value === "p" || value === "s" || value === "d" || value === "ds" || value === "f") return value;
  return null;
}

export function firstEnabledArea(areas: StudentLearningArea[]): AreaId | null {
  const match = areas.find((area) => area.enabled && normalizeAreaId(area.area_id));
  return normalizeAreaId(match?.area_id);
}

export function profileAreaId(profile: StudentLearningProfileSummary): AreaId | null {
  const mappedArea = profileAreaByChapterId[profile.chapter_id];
  if (mappedArea) return mappedArea;

  const text = `${profile.title} ${profile.subtitle} ${profile.family_name}`;
  if (text.includes("ds")) return "ds";
  if (text.includes("s区")) return "s";
  if (text.includes("p区")) return "p";
  if (text.includes("d区")) return "d";
  if (text.includes("f区")) return "f";
  return null;
}
