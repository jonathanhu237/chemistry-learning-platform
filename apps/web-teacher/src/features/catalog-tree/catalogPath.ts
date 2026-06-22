import type { CatalogBreadcrumb } from "../../api/catalogTree";
import { formatChapterTitle } from "../../lib/resourceUtils";

function compactLabel(value?: string | null): string {
  return (value || "").replace(/\s+/g, " ").trim();
}

function chapterRootLabel(chapterId?: string | null): string {
  const cleanChapterId = compactLabel(chapterId);
  return cleanChapterId ? compactLabel(formatChapterTitle(null, cleanChapterId)) : "";
}

export function catalogPathLabel(
  breadcrumbs: CatalogBreadcrumb[] = [],
  chapterId?: string | null,
  options: { includePoint?: boolean } = {},
): string {
  const includePoint = options.includePoint ?? true;
  const root = chapterRootLabel(chapterId || breadcrumbs[0]?.chapter_id);
  const rootKey = compactLabel(root);
  const titles = breadcrumbs
    .filter((item) => includePoint || item.node_kind !== "point")
    .map((item) => compactLabel(item.title))
    .filter((title) => title && title !== rootKey);

  return [root, ...titles].filter(Boolean).join(" / ");
}

export function catalogDirectoryPathLabel(breadcrumbs: CatalogBreadcrumb[] = [], chapterId?: string | null): string {
  return catalogPathLabel(breadcrumbs, chapterId, { includePoint: false });
}
