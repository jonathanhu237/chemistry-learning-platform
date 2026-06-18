import type { StudentLearningChapterExperimentGroup, StudentLearningProfile, StudentLearningProfileSummary } from "../../api";
import { escapeRegExp } from "../experiments/experimentFormat";
import { profileAreaId } from "../periodic-table/periodicHelpers";

export function chapterExperimentGroupsForProfile(profile: StudentLearningProfile): StudentLearningChapterExperimentGroup[] {
  if (profile.chapter_experiment_groups?.length) return profile.chapter_experiment_groups;

  const groups = new Map<string, StudentLearningChapterExperimentGroup>();
  for (const relatedGroup of profile.related_groups || []) {
    const groupKey = relatedGroup.parent_code || relatedGroup.parent_title;
    if (!groupKey) continue;
    const group =
      groups.get(groupKey) ||
      ({
        parent_code: relatedGroup.parent_code,
        parent_title: relatedGroup.parent_title,
        points: [],
      } satisfies StudentLearningChapterExperimentGroup);
    const seenPointKeys = new Set(group.points.map((point) => point.id || point.point_key || point.title));
    for (const point of relatedGroup.points || []) {
      const pointKey = point.id || point.point_key || point.title;
      if (!seenPointKeys.has(pointKey)) {
        group.points.push(point);
        seenPointKeys.add(pointKey);
      }
    }
    groups.set(groupKey, group);
  }
  return Array.from(groups.values()).sort((first, second) => first.parent_code.localeCompare(second.parent_code));
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
