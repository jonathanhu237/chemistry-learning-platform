import { periodicElements } from "./legacyPeriodic";
import type { StudentCatalogBreadcrumb, StudentCatalogNodeCard, StudentLearningElementBadge, StudentLearningProfile, StudentLearningProfileSummary } from "./api";

export type LegacyPeriodicElement = (typeof periodicElements)[number];
export type LegacyAreaId = "hydrogen" | "p" | "s" | "ds" | "d" | "f";

export const legacyAreaOrder: LegacyAreaId[] = ["hydrogen", "p", "s", "ds", "d", "f"];

export const legacyAreaLabels: Record<LegacyAreaId, string> = {
  hydrogen: "氢元素",
  p: "p区元素",
  s: "s区元素",
  ds: "ds区元素",
  d: "d区元素",
  f: "f区元素",
};

export const legacyAreaColors: Record<LegacyAreaId, string> = {
  hydrogen: "#fff2cc",
  p: "#eef3ff",
  s: "#edf8e9",
  ds: "#f7ecff",
  d: "#edf5f7",
  f: "#fff0f0",
};

export const legacyAreaInk: Record<LegacyAreaId, string> = {
  hydrogen: "#755400",
  p: "#1f3d73",
  s: "#285b2a",
  ds: "#5a2b73",
  d: "#244e57",
  f: "#7a2c2c",
};

const bySymbol = new Map(periodicElements.map((element) => [element.symbol.toLowerCase(), element]));

export function periodicMetaForSymbol(symbol?: string | null): LegacyPeriodicElement | null {
  if (!symbol) return null;
  return bySymbol.get(symbol.toLowerCase()) || null;
}

export function periodicAreaIdForElement(element: LegacyPeriodicElement | StudentLearningElementBadge): LegacyAreaId {
  if (element.symbol === "H") return "hydrogen";
  const block = String("block" in element ? element.block || "" : "").toLowerCase();
  const area = String("area" in element ? element.area || "" : "").toLowerCase();
  const group = Number(element.group || 0);
  if (block === "f" || area.startsWith("f")) return "f";
  if (group === 11 || group === 12 || area.startsWith("ds")) return "ds";
  if (block === "d" || area.startsWith("d")) return "d";
  if (block === "s" || area.startsWith("s")) return "s";
  return "p";
}

export function periodicGridColumn(element: LegacyPeriodicElement): number {
  return Math.max(1, Math.min(18, Number(element.group || 1)));
}

export function periodicGridRow(element: LegacyPeriodicElement): number {
  const period = Number(element.period || 1);
  return period + 1;
}

export function formatProfileTitle(profile: StudentLearningProfile | StudentLearningProfileSummary): string {
  const family = [profile.family_number, profile.family_name ? `（${profile.family_name}）` : ""].filter(Boolean).join("");
  return family || profile.title || profile.subtitle || "学习章节";
}

export function formatProfileShortTitle(profile: StudentLearningProfile | StudentLearningProfileSummary): string {
  if (profile.family_name?.trim()) return profile.family_name.trim();
  const source = [formatProfileTitle(profile), profile.title, profile.subtitle].filter(Boolean).join(" ");
  const bracketMatch = source.match(/[（(]([^（）()]+)[）)]/);
  return bracketMatch?.[1]?.trim() || profile.title || profile.subtitle || "学习章节";
}

export function profileHasArea(profile: StudentLearningProfile | StudentLearningProfileSummary, areaId: LegacyAreaId): boolean {
  return profile.element_symbols.some((symbol) => {
    const element = periodicMetaForSymbol(symbol);
    return Boolean(element && periodicAreaIdForElement(element) === areaId);
  });
}

export function catalogPathLabel(path: StudentCatalogBreadcrumb[]): string {
  return path.map((item) => item.title).filter(Boolean).join(" / ");
}

export function nodePathLabel(path: StudentCatalogBreadcrumb[], node: StudentCatalogNodeCard): string {
  return catalogPathLabel([...path, { node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }]);
}

export function findProfileForElement(element: LegacyPeriodicElement, profiles: StudentLearningProfileSummary[]): StudentLearningProfileSummary | null {
  const exactProfile = profiles.find((profile) => profile.element_symbols.some((symbol) => symbol.toLowerCase() === element.symbol.toLowerCase()));
  if (exactProfile) return exactProfile;

  const elementArea = periodicAreaIdForElement(element);
  const groupProfile = profiles.find((profile) =>
    profile.element_symbols.some((symbol) => {
      const profileElement = periodicMetaForSymbol(symbol);
      return Boolean(profileElement && profileElement.group === element.group && periodicAreaIdForElement(profileElement) === elementArea);
    }),
  );
  if (groupProfile) return groupProfile;

  const areaProfiles = profiles.filter((profile) =>
    profile.element_symbols.some((symbol) => {
      const profileElement = periodicMetaForSymbol(symbol);
      return Boolean(profileElement && periodicAreaIdForElement(profileElement) === elementArea);
    }),
  );
  return areaProfiles.length === 1 ? areaProfiles[0] : null;
}
