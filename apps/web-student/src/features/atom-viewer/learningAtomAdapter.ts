import type { StudentLearningElementBadge, StudentLearningProfile } from "../../api";
import {
  areaSwatches,
  elementEnglishName,
  periodicAreaIdForElement,
  periodicMetaForElement,
} from "../periodic-table/periodicHelpers";
import type { AtomViewerElement } from "./atomTypes";

const nobleGasShells: Record<string, number[]> = {
  He: [2],
  Ne: [2, 8],
  Ar: [2, 8, 8],
  Kr: [2, 8, 18, 8],
  Xe: [2, 8, 18, 18, 8],
  Rn: [2, 8, 18, 32, 18, 8],
  Og: [2, 8, 18, 32, 32, 18, 8],
};

const shellCapacities = [2, 8, 18, 32, 32, 18, 8];
const superscriptDigits: Record<string, string> = {
  "⁰": "0",
  "¹": "1",
  "²": "2",
  "³": "3",
  "⁴": "4",
  "⁵": "5",
  "⁶": "6",
  "⁷": "7",
  "⁸": "8",
  "⁹": "9",
};

const stateLabel: Record<string, string> = {
  Gas: "气体",
  Solid: "固体",
  Liquid: "液体",
};

function normalizeConfiguration(configuration: string) {
  return configuration
    .replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (digit) => superscriptDigits[digit] || digit)
    .replace(/\s+/g, " ")
    .trim();
}

function shellsFromAtomicNumber(atomicNumber: number) {
  let remaining = Math.max(0, atomicNumber);
  const shells: number[] = [];
  for (const capacity of shellCapacities) {
    if (remaining <= 0) break;
    const count = Math.min(capacity, remaining);
    shells.push(count);
    remaining -= count;
  }
  if (remaining > 0) {
    shells.push(remaining);
  }
  return shells;
}

export function deriveElectronShells(configuration: string | null | undefined, atomicNumber?: number | null) {
  const normalized = normalizeConfiguration(configuration || "");
  const shells: number[] = [];
  const coreMatch = normalized.match(/\[([A-Z][a-z]?)\]/);
  if (coreMatch) {
    nobleGasShells[coreMatch[1]]?.forEach((count, index) => {
      shells[index] = count;
    });
  }

  let matchedSubshell = false;
  const source = normalized.replace(/\[[^\]]+\]/g, " ");
  const subshellRegex = /(\d+)\s*([spdf])\s*(\d+)/g;
  let match: RegExpExecArray | null;
  while ((match = subshellRegex.exec(source)) !== null) {
    const shellIndex = Number.parseInt(match[1], 10) - 1;
    const electronCount = Number.parseInt(match[3], 10);
    if (!Number.isFinite(shellIndex) || shellIndex < 0 || !Number.isFinite(electronCount)) continue;
    shells[shellIndex] = (shells[shellIndex] || 0) + electronCount;
    matchedSubshell = true;
  }

  const compact = shells.map((count) => count || 0);
  while (compact.length && compact[compact.length - 1] === 0) {
    compact.pop();
  }

  if (compact.length && matchedSubshell) {
    return compact;
  }
  return atomicNumber ? shellsFromAtomicNumber(atomicNumber) : [];
}

function blockForElement(element: StudentLearningElementBadge): AtomViewerElement["block"] {
  const source = String(element.block || "").trim().toLowerCase();
  if (source === "s" || source === "p" || source === "d" || source === "f") return source;
  const periodic = periodicMetaForElement(element.symbol);
  const fallback = String(periodic?.area || "").slice(0, 1);
  return fallback === "s" || fallback === "p" || fallback === "d" || fallback === "f" ? fallback : "p";
}

function displayStateAt20C(value: string | null | undefined) {
  if (!value) return "未整理";
  return stateLabel[value] || value;
}

function displayDensity(value: string | null | undefined) {
  if (!value) return "未整理";
  if (value.trim().toLowerCase().startsWith("unknown")) return "未知";
  return value;
}

export function learningElementToAtomModel(
  element: StudentLearningElementBadge,
  profile: StudentLearningProfile,
): AtomViewerElement {
  const periodic = periodicMetaForElement(element.symbol);
  const areaId = periodic ? periodicAreaIdForElement(periodic) : null;
  const atomicNumber = element.atomic_number ?? periodic?.atomicNumber ?? 0;
  const electronConfiguration = normalizeConfiguration(element.electron_configuration || "");
  const shells = deriveElectronShells(electronConfiguration, atomicNumber);
  const missing: string[] = [];
  if (!atomicNumber) missing.push("原子序数");
  if (!electronConfiguration) missing.push("电子排布");
  if (!shells.length) missing.push("电子层");

  return {
    atomicNumber,
    symbol: element.symbol,
    name: element.name,
    englishName: elementEnglishName(element),
    category: profile.family_name || profile.title || element.group_label || "",
    group: element.group || periodic?.group?.toString() || "",
    period: element.period ?? periodic?.period ?? 0,
    block: blockForElement(element),
    stateAt20C: displayStateAt20C(element.state_at_20c),
    density: displayDensity(element.density),
    oxidationStates: element.common_valence || "未整理",
    relativeAtomicMass: element.relative_atomic_mass || "未整理",
    electronConfiguration,
    shells,
    accent: areaId ? areaSwatches[areaId] : "#0f7b4d",
    sourceUrl: element.rsc_url || null,
    sourceLabel: element.fact_source || "Royal Society of Chemistry Periodic Table",
    teachingNote: element.note || "",
    redoxTendency: element.redox_tendency || "",
    unavailableReason: missing.length ? `缺少${missing.join("、")}数据，暂时无法生成可旋转模型。` : undefined,
  };
}
