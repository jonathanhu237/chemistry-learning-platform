import type {
  CatalogChapterTreeSummary,
  CatalogMissingLearningFieldKey,
  CatalogNodeCard,
  CatalogNodeCreatePayload,
  CatalogNodeDetail,
  CatalogNodeKind,
  CatalogNodeMovePayload,
  CatalogNodePrimaryState,
  CatalogNodeStatusSummary,
  CatalogNodeUpdatePayload,
  CatalogPointContentPayload,
  CatalogPrincipleMode,
  CatalogReactionEquationInput,
  CatalogReactionEquationNormalized,
  CatalogRelatedLinksPayload,
} from "../../api/catalogTree";

export type CatalogNodeFormValues = {
  title: string;
  summary?: string;
  node_kind: CatalogNodeKind;
  teacher_note?: string;
  canonical_point_id?: string;
};

export type CatalogPointContentFormValues = {
  point_title: string;
  teacher_note?: string;
  principle_mode: CatalogPrincipleMode;
  principle_equation?: string;
  reaction_equations_text?: string;
  reaction_equations?: CatalogReactionEquationInput[];
  principle_text?: string;
  phenomenon_explanation?: string;
  safety_note?: string;
};

export type CatalogRelatedLinkFormItem = {
  target_node_id?: string;
  target_title?: string;
  relation_type?: "manual" | "default_override" | "generated_default";
  source?: string;
  hidden?: boolean;
  sort_order?: number;
  metadata?: Record<string, unknown>;
};

export type CatalogRelatedLinksFormValues = {
  links?: CatalogRelatedLinkFormItem[];
};

export function isPointCapable(kind?: CatalogNodeKind | null): boolean {
  return kind === "point";
}

export function hydrateCatalogNodeForm(detail: CatalogNodeDetail | null | undefined): CatalogNodeFormValues {
  const node = detail?.node;
  return {
    title: node?.title || "",
    summary: node?.summary || "",
    node_kind: node?.node_kind || "directory",
    teacher_note: node?.teacher_note || node?.summary || "",
    canonical_point_id: node?.canonical_point_id || "",
  };
}

export function buildCatalogNodeCreatePayload(values: CatalogNodeFormValues, chapterId: string, parentId?: string | null): CatalogNodeCreatePayload {
  return {
    chapter_id: chapterId,
    parent_id: parentId || null,
    node_kind: values.node_kind,
    title: values.title.trim(),
    summary: values.summary?.trim() || "",
    teacher_note: values.teacher_note?.trim() || "",
    canonical_point_id: values.node_kind === "point" ? values.canonical_point_id?.trim() || null : null,
  };
}

export function buildCatalogNodeUpdatePayload(values: CatalogNodeFormValues): CatalogNodeUpdatePayload {
  return {
    title: values.title.trim(),
    summary: values.summary?.trim() || "",
    node_kind: values.node_kind,
    teacher_note: values.teacher_note?.trim() || "",
  };
}

export function hydrateCatalogPointContentForm(detail: CatalogNodeDetail | null | undefined): CatalogPointContentFormValues {
  const content = detail?.point_content;
  const editorTextForEquation = (equation: CatalogReactionEquationNormalized): string => {
    const annotation = equation.annotation_text?.trim();
    if (!annotation) return equation.raw_text || equation.canonical_display || "";
    const core = equation.equation_core?.trim() || equation.raw_text?.split("//")[0]?.trim() || equation.canonical_display || "";
    return core ? `${core} // ${annotation}` : equation.raw_text || equation.canonical_display || "";
  };
  const reactionEquations =
    content?.reaction_equations?.length
      ? content.reaction_equations.map((equation, index) => ({
          raw_text: editorTextForEquation(equation),
          row_order: equation.row_order || index + 1,
        }))
      : content?.principle_equation
        ? [{ raw_text: content.principle_equation, row_order: 1 }]
        : [];
  return {
    point_title: content?.point_title || detail?.node.title || "",
    teacher_note: content?.teacher_note || "",
    principle_mode: content?.principle_mode || "text",
    principle_equation: content?.principle_equation || "",
    reaction_equations_text: reactionEquations.map((equation) => equation.raw_text).filter(Boolean).join("\n"),
    reaction_equations: reactionEquations,
    principle_text: content?.principle_text || "",
    phenomenon_explanation: content?.phenomenon_explanation || "",
    safety_note: content?.safety_note || "",
  };
}

export function displayCatalogPointTitle(detail: CatalogNodeDetail | null | undefined): string {
  return detail?.point_content?.point_title?.trim() || detail?.node.title || "";
}

export function hasDivergentPointTitle(detail: CatalogNodeDetail | null | undefined): boolean {
  const nodeTitle = detail?.node.title?.trim();
  const pointTitle = detail?.point_content?.point_title?.trim();
  return Boolean(nodeTitle && pointTitle && nodeTitle !== pointTitle);
}

export function buildCatalogPointContentPayload(values: CatalogPointContentFormValues): CatalogPointContentPayload {
  const principleMode = values.principle_mode || "text";
  const rowsFromText = (values.reaction_equations_text || "")
    .split(/\r?\n/)
    .map((rawText, index) => ({ raw_text: rawText.trim(), row_order: index + 1, metadata: {} }))
    .filter((equation) => equation.raw_text);
  const reactionEquations = (rowsFromText.length ? rowsFromText : values.reaction_equations || [])
    .map((equation, index) => ({
      raw_text: equation.raw_text?.trim() || "",
      row_order: index + 1,
      metadata: equation.metadata || {},
    }))
    .filter((equation) => equation.raw_text);
  const legacyEquationText = reactionEquations.map((equation) => equation.raw_text).join("\n");
  return {
    point_title: values.point_title.trim(),
    teacher_note: values.teacher_note?.trim() || "",
    principle_mode: principleMode,
    principle_equation: principleMode === "equation" ? legacyEquationText || values.principle_equation?.trim() || "" : "",
    reaction_equations: principleMode === "equation" ? reactionEquations : [],
    principle_text: principleMode === "text" ? values.principle_text?.trim() || "" : "",
    phenomenon_explanation: values.phenomenon_explanation?.trim() || "",
    safety_note: values.safety_note?.trim() || "",
  };
}

export function hydrateCatalogRelatedLinksForm(detail: CatalogNodeDetail | null | undefined): CatalogRelatedLinksFormValues {
  return {
    links: (detail?.related_links || []).map((link, index) => ({
      target_node_id: link.target_node_id,
      target_title: link.target_title || link.target_node_id,
      relation_type: link.relation_type === "default_override" ? "default_override" : link.relation_type === "generated_default" ? "generated_default" : "manual",
      source: link.source || link.relation_type,
      hidden: Boolean(link.hidden),
      sort_order: link.sort_order || index + 1,
      metadata: link.metadata || {},
    })),
  };
}

export function buildCatalogRelatedLinksPayload(values: CatalogRelatedLinksFormValues): CatalogRelatedLinksPayload {
  const seen = new Set<string>();
  const links: CatalogRelatedLinksPayload["links"] = [];
  (values.links || []).forEach((link, index) => {
      const targetNodeId = String(link.target_node_id || "").trim();
      if (!targetNodeId || seen.has(targetNodeId)) return;
      seen.add(targetNodeId);
      const relationType = link.relation_type === "generated_default" ? "default_override" : link.relation_type || "manual";
      links.push({
        target_node_id: targetNodeId,
        relation_type: relationType,
        hidden: Boolean(link.hidden),
        sort_order: index + 1,
        metadata: link.metadata || {},
      });
    });
  return { links };
}

export function buildMovePayload(parentId: string | null | undefined, displayOrder?: number | null): CatalogNodeMovePayload {
  return {
    parent_id: parentId || null,
    display_order: displayOrder ?? null,
  };
}

export function siblingReorderItems(siblings: CatalogNodeCard[], movedNodeId: string, direction: "up" | "down"): Array<{ node_id: string; display_order: number }> {
  const ordered = [...siblings].sort((left, right) => left.display_order - right.display_order || left.title.localeCompare(right.title));
  const index = ordered.findIndex((node) => node.node_id === movedNodeId);
  const targetIndex = direction === "up" ? index - 1 : index + 1;
  if (index < 0 || targetIndex < 0 || targetIndex >= ordered.length) return [];
  const [moved] = ordered.splice(index, 1);
  ordered.splice(targetIndex, 0, moved);
  return ordered.map((node, orderIndex) => ({ node_id: node.node_id, display_order: orderIndex + 1 }));
}

export function catalogNodeKindLabel(kind: CatalogNodeKind): string {
  const labels: Record<CatalogNodeKind, string> = {
    directory: "目录",
    point: "点位",
  };
  return labels[kind];
}

export function catalogStatusColor(status: string): string {
  if (status === "published") return "green";
  if (status === "archived") return "default";
  return "default";
}

export function catalogStatusLabel(status: string): string {
  if (status === "published") return "已发布";
  if (status === "archived") return "已归档";
  return "草稿";
}

export function catalogStatusDotClass(status: string): string {
  if (status === "published") return "is-published";
  if (status === "archived") return "is-archived";
  return "is-ready";
}

export type CatalogStatusFilter =
  | "all"
  | "actionable"
  | "blocked"
  | "needs_content"
  | "missing_principle"
  | "missing_phenomenon"
  | "missing_safety"
  | "needs_video"
  | "unpublished"
  | "published"
  | "sync_attention";

export const catalogMissingLearningFieldLabels: Record<CatalogMissingLearningFieldKey, string> = {
  principle: "实验原理",
  phenomenon: "现象解释",
  safety: "安全提示",
};

const catalogMissingFieldFilterKeys: Record<Extract<CatalogStatusFilter, "missing_principle" | "missing_phenomenon" | "missing_safety">, CatalogMissingLearningFieldKey> = {
  missing_principle: "principle",
  missing_phenomenon: "phenomenon",
  missing_safety: "safety",
};

export const catalogPrimaryStatusFilterOptions: Array<{ value: CatalogStatusFilter; label: string }> = [
  { value: "all", label: "全部" },
  { value: "actionable", label: "待处理" },
  { value: "blocked", label: "异常" },
  { value: "needs_content", label: "缺内容" },
  { value: "needs_video", label: "缺视频" },
  { value: "unpublished", label: "待发布" },
  { value: "published", label: "已发布" },
  { value: "sync_attention", label: "同步异常" },
];

export const catalogMissingFieldFilterOptions: Array<{ value: CatalogStatusFilter; label: string }> = [
  { value: "missing_principle", label: "缺实验原理" },
  { value: "missing_phenomenon", label: "缺现象解释" },
  { value: "missing_safety", label: "缺安全提示" },
];

export const catalogStatusFilterOptions: Array<{ value: CatalogStatusFilter; label: string }> = [
  ...catalogPrimaryStatusFilterOptions,
  ...catalogMissingFieldFilterOptions,
];

function isCatalogNodeDetail(value: CatalogNodeCard | CatalogNodeDetail): value is CatalogNodeDetail {
  return Boolean((value as CatalogNodeDetail).node);
}

function fallbackStatusForNode(node: CatalogNodeCard): CatalogNodeStatusSummary {
  const hasStructureErrors = Boolean(node.validation?.errors?.length);
  const hasContent = Boolean(node.has_point_content);
  const hasVideo = node.node_kind === "point" ? node.media_count > 0 : true;
  const primaryState: CatalogNodePrimaryState =
    node.status === "archived"
      ? "archived"
      : hasStructureErrors
        ? "blocked"
        : node.node_kind === "point" && !hasContent
          ? "needs_content"
          : node.node_kind === "point" && !hasVideo
            ? "needs_video"
            : node.status === "published"
              ? "published"
              : node.node_kind === "point"
                ? "ready"
                : "draft";
  return {
    primary_state: primaryState,
    primary_label: catalogNodePrimaryStateLabel(primaryState),
    primary_reason:
      primaryState === "blocked"
        ? "点位结构需要处理"
        : primaryState === "needs_content"
          ? "三要素尚未填写"
        : primaryState === "needs_video"
          ? "无视频"
          : catalogNodePrimaryStateLabel(primaryState),
    core_readiness: {
      content_fields: hasContent ? "complete" : "missing",
      video: hasVideo ? "present" : "absent",
      video_label: hasVideo ? "有视频" : "无视频",
      missing_field_keys: [],
      missing_field_labels: [],
      missing_fields: [],
      descendant_action_count: 0,
      descendant_status_counts: {},
      descendant_missing_field_counts: {},
    },
    visibility: {
      placement: node.status,
      shared_content: node.node_kind === "point" ? (hasContent ? node.status : "missing") : "not_applicable",
      student_available: node.status === "published" && !hasStructureErrors,
    },
    async_consumption: {
      search_index: node.index_state?.sync_status === "synced" ? "synced" : node.index_state?.sync_status || "idle",
      ai_evidence: "idle",
    },
    conditions: [],
  };
}

export function resolveCatalogNodeStatus(source: CatalogNodeCard | CatalogNodeDetail): CatalogNodeStatusSummary {
  if (isCatalogNodeDetail(source)) {
    return source.node_status || source.node.node_status || fallbackStatusForNode(source.node);
  }
  return source.node_status || fallbackStatusForNode(source);
}

export function catalogNodePrimaryStateLabel(state: string): string {
  const labels: Record<string, string> = {
    archived: "已归档",
    blocked: "异常",
    needs_content: "缺内容",
    needs_video: "缺视频",
    draft: "草稿",
    ready: "待发布",
    published: "已发布",
    sync_attention: "同步异常",
  };
  return labels[state] || "未知状态";
}

export function catalogNodePrimaryStateClass(state: string): string {
  if (state === "published") return "is-published";
  if (state === "ready") return "is-ready";
  if (state === "archived") return "is-archived";
  if (state === "blocked") return "is-error";
  if (state === "sync_attention") return "is-sync";
  if (state === "needs_content" || state === "needs_video") return "is-warning";
  return "is-draft";
}

export type CatalogHeaderPrimaryActionKey =
  | "restore"
  | "view-issues"
  | "edit-content"
  | "publish-content"
  | "bind-video"
  | "publish-placement"
  | "view-sync"
  | "preview-student";

export type CatalogHeaderPrimaryAction = {
  key: CatalogHeaderPrimaryActionKey;
  label: string;
  tone: "primary" | "warning" | "danger" | "default";
};

export function catalogHeaderPrimaryAction(detail: CatalogNodeDetail): CatalogHeaderPrimaryAction | null {
  const { node } = detail;
  const status = resolveCatalogNodeStatus(detail);
  const primaryState = status.primary_state;

  if (primaryState === "archived" || node.status === "archived") {
    return { key: "restore", label: isPointCapable(node.node_kind) ? "恢复点位" : "恢复目录", tone: "default" };
  }
  if (primaryState === "blocked") {
    return { key: "view-issues", label: "查看问题", tone: "warning" };
  }

  if (isPointCapable(node.node_kind)) {
    if (status.core_readiness.content_fields === "missing" || primaryState === "needs_content") {
      return { key: "edit-content", label: "编辑内容", tone: "primary" };
    }
    if (status.core_readiness.video === "absent" || primaryState === "needs_video") {
      return { key: "bind-video", label: "绑定视频", tone: "primary" };
    }
    if (status.visibility.shared_content !== "published") {
      return { key: "publish-content", label: "发布学习内容", tone: "primary" };
    }
    if (status.visibility.placement !== "published") {
      return { key: "publish-placement", label: "发布到学生端", tone: "primary" };
    }
    if (
      primaryState === "sync_attention" ||
      ["failed", "unavailable"].includes(status.async_consumption.search_index) ||
      ["failed", "unavailable"].includes(status.async_consumption.ai_evidence)
    ) {
      return { key: "view-sync", label: "查看同步", tone: "warning" };
    }
    return { key: "preview-student", label: "预览学生端", tone: "primary" };
  }

  if (["needs_content", "needs_video", "sync_attention"].includes(primaryState)) {
    return { key: primaryState === "sync_attention" ? "view-sync" : "view-issues", label: primaryState === "sync_attention" ? "查看同步" : "查看问题", tone: "warning" };
  }
  if (node.status !== "published") {
    return { key: "publish-placement", label: "发布目录", tone: "primary" };
  }
  return { key: "preview-student", label: "预览学生端", tone: "primary" };
}

export function catalogMissingFieldKeys(status: CatalogNodeStatusSummary): CatalogMissingLearningFieldKey[] {
  const explicitKeys = status.core_readiness.missing_field_keys || [];
  const normalized = explicitKeys.filter((key): key is CatalogMissingLearningFieldKey => key === "principle" || key === "phenomenon" || key === "safety");
  if (normalized.length) return normalized;
  const legacyLabels = status.core_readiness.missing_field_labels || status.core_readiness.missing_fields || [];
  return legacyLabels
    .map((label) => {
      if (label === "实验原理" || label === "原理") return "principle";
      if (label === "现象解释") return "phenomenon";
      if (label === "安全提示") return "safety";
      return null;
    })
    .filter((key): key is CatalogMissingLearningFieldKey => Boolean(key));
}

function missingFieldFilterKey(filter: CatalogStatusFilter): CatalogMissingLearningFieldKey | null {
  return filter === "missing_principle" || filter === "missing_phenomenon" || filter === "missing_safety"
    ? catalogMissingFieldFilterKeys[filter]
    : null;
}

export function catalogNodeActionCount(node: CatalogNodeCard): number {
  const status = resolveCatalogNodeStatus(node);
  const counts = status.core_readiness.descendant_status_counts || {};
  const aggregate =
    Number(counts.blocked || 0) +
    Number(counts.needs_content || 0) +
    Number(counts.needs_video || 0) +
    Number(counts.ready || 0) +
    Number(counts.draft || 0) +
    Number(counts.sync_attention || 0);
  return node.node_kind === "directory" ? Math.max(Number(status.core_readiness.descendant_action_count ?? 0), aggregate) : 0;
}

export type CatalogDirectoryPendingPart = {
  key: "blocked" | "needs_content" | "needs_video" | "draft" | "sync_attention";
  label: string;
  count: number;
  severity: "error" | "warning" | "sync";
};

export function catalogNodeDirectoryPendingParts(node: CatalogNodeCard): CatalogDirectoryPendingPart[] {
  if (node.node_kind !== "directory") return [];
  const status = resolveCatalogNodeStatus(node);
  const counts = status.core_readiness.descendant_status_counts || {};
  const countFor = (key: string) => Number(counts[key] || 0);
  const parts: CatalogDirectoryPendingPart[] = [
    { key: "blocked", label: "阻断", count: countFor("blocked"), severity: "error" },
    { key: "needs_content", label: "缺内容", count: countFor("needs_content"), severity: "warning" },
    { key: "needs_video", label: "缺视频", count: countFor("needs_video"), severity: "warning" },
    { key: "draft", label: "草稿", count: countFor("draft"), severity: "warning" },
    { key: "sync_attention", label: "同步异常", count: countFor("sync_attention"), severity: "sync" },
  ];
  return parts.filter((item) => item.count > 0);
}

export function catalogNodeDirectoryPendingCount(node: CatalogNodeCard): number {
  return catalogNodeDirectoryPendingParts(node).reduce((total, item) => total + item.count, 0);
}

export function catalogNodeDirectoryPendingLabel(node: CatalogNodeCard): string {
  const parts = catalogNodeDirectoryPendingParts(node);
  const total = parts.reduce((sum, item) => sum + item.count, 0);
  if (!total) return "";
  const detail = parts.map((item) => `${item.count} 个${item.label}`).join("，");
  return `待处理：${total} 个点位（${detail}）`;
}

export function catalogNodeDirectoryPendingClass(node: CatalogNodeCard): string {
  const parts = catalogNodeDirectoryPendingParts(node);
  if (parts.some((item) => item.severity === "error")) return "is-error";
  if (parts.some((item) => item.severity === "sync")) return "is-sync";
  return parts.length ? "is-warning" : catalogStatusDotClass(node.status);
}

export function catalogNodeStatusTooltip(node: CatalogNodeCard | CatalogNodeDetail): string {
  const status = resolveCatalogNodeStatus(node);
  const label = status.primary_label || catalogNodePrimaryStateLabel(status.primary_state);
  const reason = status.primary_reason || label;
  return reason === label ? label : `${label}：${reason}`;
}

export function matchesCatalogNodeStatusFilter(node: CatalogNodeCard, filter: CatalogStatusFilter): boolean {
  if (filter === "all") return true;
  const status = resolveCatalogNodeStatus(node);
  const state = status.primary_state;
  const counts = status.core_readiness.descendant_status_counts || {};
  const missingFieldKey = missingFieldFilterKey(filter);
  if (missingFieldKey) {
    if (node.node_kind === "directory") {
      const missingCounts = status.core_readiness.descendant_missing_field_counts || {};
      return Number(missingCounts[missingFieldKey] || counts[`missing_${missingFieldKey}`] || 0) > 0;
    }
    return state === "needs_content" && catalogMissingFieldKeys(status).includes(missingFieldKey);
  }
  if (node.node_kind === "directory") {
    if (filter === "published") return Number(counts.published || 0) > 0;
    if (filter === "blocked") return Number(counts.blocked || 0) > 0;
    if (filter === "unpublished") return Number(counts.draft || 0) > 0 || Number(counts.ready || 0) > 0;
    if (filter === "needs_content") return Number(counts.needs_content || 0) > 0;
    if (filter === "needs_video") return Number(counts.needs_video || 0) > 0;
    if (filter === "sync_attention") return Number(counts.sync_attention || 0) > 0;
    return catalogNodeActionCount(node) > 0;
  }
  if (filter === "published") return state === "published";
  if (filter === "blocked") return state === "blocked";
  if (filter === "unpublished") return state === "draft" || state === "ready";
  if (filter === "needs_content") return state === "needs_content";
  if (filter === "needs_video") return state === "needs_video";
  if (filter === "sync_attention") {
    return state === "sync_attention";
  }
  return (
    state === "blocked" ||
    state === "needs_content" ||
    state === "needs_video" ||
    state === "draft" ||
    state === "ready" ||
    catalogNodeActionCount(node) > 0
  );
}

export function catalogStatusFilterCount(summary: CatalogChapterTreeSummary | null | undefined, filter: CatalogStatusFilter): number | null {
  if (!summary) return null;
  const pointCounts = summary.point_status_counts || {};
  const missingFieldKey = missingFieldFilterKey(filter);
  if (missingFieldKey) return Number(summary.point_missing_field_counts?.[missingFieldKey] || 0);
  if (filter === "all") return summary.point_count;
  if (filter === "actionable") return summary.actionable_point_count;
  if (filter === "blocked") return Number(pointCounts.blocked || 0);
  if (filter === "needs_content") return Number(pointCounts.needs_content || 0);
  if (filter === "needs_video") return Number(pointCounts.needs_video || 0);
  if (filter === "unpublished") return Number(pointCounts.ready || 0) + Number(pointCounts.draft || 0);
  if (filter === "published") return Number(pointCounts.published || 0);
  if (filter === "sync_attention") return Number(pointCounts.sync_attention || 0);
  return null;
}
