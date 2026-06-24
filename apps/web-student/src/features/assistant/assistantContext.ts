import type {
  StudentAssistantAskRequest,
  StudentCatalogBreadcrumb,
  StudentCatalogNodeCard,
  StudentVideoLibraryResultItem,
  StudentVideoLibraryRouteTarget,
} from "../../api";

export type AssistantContext = Omit<StudentAssistantAskRequest, "question" | "conversation_history"> & { prompts: string[] };

function cleanText(value: string | null | undefined): string {
  return String(value || "").trim();
}

function compactText(parts: Array<string | null | undefined>, maxLength = 1800): string {
  return parts
    .map(cleanText)
    .filter(Boolean)
    .join(" · ")
    .slice(0, maxLength);
}

function uniquePath(parts: Array<string | null | undefined>): string[] {
  const result: string[] = [];
  for (const part of parts) {
    const text = cleanText(part);
    if (!text) continue;
    if (result[result.length - 1] === text) continue;
    result.push(text);
  }
  return result;
}

function promptTitle(title: string): string {
  return cleanText(title) || "这个实验点位";
}

export function defaultAssistantContext(): AssistantContext {
  return {
    context_type: "learning_home",
    context_title: "Atom 学习助手",
    context_summary: "学生端全局课程问答入口",
    prompts: ["我应该先复习哪一个概念？", "帮我解释一个无机化学实验现象", "怎样把元素性质和实验现象联系起来？"],
  };
}

export function isPointAssistantContext(context: AssistantContext): boolean {
  return (
    context.context_type === "learning_point" &&
    Boolean(context.point_node_id || context.source_node_id || context.chapter_id || context.catalog_path?.length)
  );
}

export function assistantContextPathLabel(context: AssistantContext): string {
  return uniquePath(context.catalog_path || []).join(" / ");
}

export function isBindableVideoLibraryResult(item: StudentVideoLibraryResultItem): boolean {
  const target = item.target;
  return Boolean(target && target.kind === "point_detail" && (target.node_id || target.placement_node_id));
}

export function assistantContextFromVideoLibraryResult(item: StudentVideoLibraryResultItem): AssistantContext | null {
  const target = item.target;
  if (!target || !isBindableVideoLibraryResult(item)) return null;
  return assistantContextFromVideoLibraryTarget(item, target);
}

export function assistantContextFromVideoLibraryTarget(
  item: Pick<StudentVideoLibraryResultItem, "title" | "subtitle" | "snippet">,
  target: StudentVideoLibraryRouteTarget,
): AssistantContext {
  const title = target.context_title || target.point_title || item.title;
  const path = uniquePath(target.catalog_path || []);
  const summary = compactText([
    path.length ? `目录路径：${path.join(" / ")}` : null,
    target.context_summary,
    item.snippet,
    item.subtitle,
  ]);
  return {
    context_type: "learning_point",
    context_title: title,
    context_summary: summary,
    chapter_id: target.chapter_id || undefined,
    point_node_id: target.node_id || target.placement_node_id || undefined,
    source_node_id: target.source_node_id || undefined,
    catalog_path: path.length ? path : undefined,
    prompts: [
      target.prompt || `解释「${promptTitle(title)}」这个实验现象`,
      "这个现象对应的原理是什么？",
      "学习这个点位要注意哪些步骤？",
    ],
  };
}

export function assistantContextFromCatalogNode(
  node: StudentCatalogNodeCard,
  breadcrumbs: StudentCatalogBreadcrumb[],
  rootTitle?: string | null,
): AssistantContext {
  const path = uniquePath([rootTitle, ...breadcrumbs.map((item) => item.title), node.title]);
  const title = node.canonical_point_title || node.title;
  return {
    context_type: "learning_point",
    context_title: title,
    context_summary: compactText([
      path.length ? `目录路径：${path.join(" / ")}` : null,
      node.summary,
      node.published_media_count || node.media_count ? "包含可学习的视频点位内容" : null,
    ]),
    chapter_id: node.chapter_id || breadcrumbs[0]?.chapter_id || undefined,
    point_node_id: node.placement_node_id || node.node_id || undefined,
    source_node_id: node.node_id || undefined,
    catalog_path: path.length ? path : undefined,
    prompts: [
      `解释「${promptTitle(title)}」这个实验现象`,
      "这个点位的步骤和原理怎么对应？",
      "学习这个点位容易错在哪里？",
    ],
  };
}
