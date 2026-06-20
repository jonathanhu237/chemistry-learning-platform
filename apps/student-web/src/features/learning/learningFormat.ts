import type { StudentLearningProfileSummary } from "../../api";
import { profileAreaId } from "../periodic-table/periodicHelpers";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function stripFamilyNumberPrefix(title: string, familyNumber?: string | null): string {
  if (!familyNumber) return title;
  const escapedFamilyNumber = escapeRegExp(familyNumber);
  const stripped = title
    .replace(new RegExp(`^第\\s*${escapedFamilyNumber}\\s*族\\s*`), "")
    .replace(new RegExp(`^${escapedFamilyNumber}\\s*族\\s*`), "")
    .trim();
  return stripped || title;
}

export function formatFamilyNumberLabel(familyNumber?: string | null): string {
  const normalized = familyNumber?.trim();
  if (!normalized || !/^\d+$/.test(normalized)) return "";
  const parsed = Number.parseInt(normalized, 10);
  return parsed >= 1 && parsed <= 18 ? `${parsed}族` : "";
}

export function formatChapterEntryTitle(profile: StudentLearningProfileSummary): string {
  const title = stripFamilyNumberPrefix(profile.title, profile.family_number);
  const familyLabel = formatFamilyNumberLabel(profile.family_number);
  if (!familyLabel) return formatAreaProfileLabel(profile);
  return `${familyLabel}${formatNicknameParentheses(title)}`;
}

export function formatNicknameParentheses(value: string): string {
  const title = value.trim();
  if (/^（.+）$/.test(title)) return title;
  const asciiWrapped = title.match(/^\((.+)\)$/);
  if (asciiWrapped) return `（${asciiWrapped[1]}）`;
  return title ? `（${title}）` : "";
}

export function stripLearningChapterPrefix(value: string): string {
  return value.replace(/^第\s*\d+\s*章\s*/, "").trim() || value;
}

export function formatAreaProfileLabel(profile: StudentLearningProfileSummary): string {
  if (profileAreaId(profile) === "integrated") return "氢和稀有气体";

  const rawLabel = profile.family_name || profile.title || profile.subtitle || "";
  const withoutChapter = stripLearningChapterPrefix(rawLabel).trim();
  const parenthesizedAreaLabel = withoutChapter.match(/^(?:s|p|d|ds|f)\s*区\s*[（(](.+)[）)]$/i);
  const label = (parenthesizedAreaLabel?.[1] || withoutChapter)
    .replace(/^(?:s|p|d|ds|f)\s*区\s*/i, "")
    .replace(/元素$/g, "")
    .replace(/\s+/g, "")
    .trim();
  return label || withoutChapter || profile.title;
}

export function formatRecommendedAreaCueLabel(profile: StudentLearningProfileSummary | null): string | null {
  if (!profile) return null;
  if (profileAreaId(profile) === "integrated") return "氢和稀有气体";

  const familyLabel = formatFamilyNumberLabel(profile.family_number);
  if (familyLabel) return familyLabel;

  return formatAreaProfileLabel(profile);
}
