import type {
  CatalogNodeCard,
  CatalogNodeCreatePayload,
  CatalogNodeDetail,
  CatalogNodeKind,
  CatalogNodeMovePayload,
  CatalogNodeUpdatePayload,
  CatalogPointContentPayload,
  CatalogPrincipleMode,
  CatalogRelatedLinksPayload,
} from "../../api/catalogTree";

export type CatalogNodeFormValues = {
  title: string;
  summary?: string;
  node_kind: CatalogNodeKind;
  shortcut_target_node_id?: string;
};

export type CatalogPointContentFormValues = {
  point_title: string;
  teacher_note?: string;
  principle_mode: CatalogPrincipleMode;
  principle_equation?: string;
  principle_text?: string;
  phenomenon_explanation?: string;
  safety_note?: string;
};

export type CatalogRelatedLinkFormItem = {
  target_node_id?: string;
  relation_type?: "manual" | "default_override" | "generated_default";
  hidden?: boolean;
  sort_order?: number;
  label?: string;
};

export type CatalogRelatedLinksFormValues = {
  links?: CatalogRelatedLinkFormItem[];
};

export function isPointCapable(kind?: CatalogNodeKind | null): boolean {
  return kind === "point" || kind === "hybrid";
}

export function hydrateCatalogNodeForm(detail: CatalogNodeDetail | null | undefined): CatalogNodeFormValues {
  const node = detail?.node;
  return {
    title: node?.title || "",
    summary: node?.summary || "",
    node_kind: node?.node_kind || "directory",
    shortcut_target_node_id: node?.shortcut_target_node_id || "",
  };
}

export function buildCatalogNodeCreatePayload(values: CatalogNodeFormValues, chapterId: string, parentId?: string | null): CatalogNodeCreatePayload {
  return {
    chapter_id: chapterId,
    parent_id: parentId || null,
    node_kind: values.node_kind,
    title: values.title.trim(),
    summary: values.summary?.trim() || "",
    shortcut_target_node_id: values.node_kind === "shortcut" ? values.shortcut_target_node_id?.trim() || null : null,
  };
}

export function buildCatalogNodeUpdatePayload(values: CatalogNodeFormValues): CatalogNodeUpdatePayload {
  return {
    title: values.title.trim(),
    summary: values.summary?.trim() || "",
    node_kind: values.node_kind,
    shortcut_target_node_id: values.node_kind === "shortcut" ? values.shortcut_target_node_id?.trim() || null : null,
  };
}

export function hydrateCatalogPointContentForm(detail: CatalogNodeDetail | null | undefined): CatalogPointContentFormValues {
  const content = detail?.point_content;
  return {
    point_title: content?.point_title || detail?.node.title || "",
    teacher_note: content?.teacher_note || "",
    principle_mode: content?.principle_mode || "text",
    principle_equation: content?.principle_equation || "",
    principle_text: content?.principle_text || "",
    phenomenon_explanation: content?.phenomenon_explanation || "",
    safety_note: content?.safety_note || "",
  };
}

export function buildCatalogPointContentPayload(values: CatalogPointContentFormValues): CatalogPointContentPayload {
  const principleMode = values.principle_mode || "text";
  return {
    point_title: values.point_title.trim(),
    teacher_note: values.teacher_note?.trim() || "",
    principle_mode: principleMode,
    principle_equation: principleMode === "equation" ? values.principle_equation?.trim() || "" : "",
    principle_text: principleMode === "text" ? values.principle_text?.trim() || "" : "",
    phenomenon_explanation: values.phenomenon_explanation?.trim() || "",
    safety_note: values.safety_note?.trim() || "",
  };
}

export function hydrateCatalogRelatedLinksForm(detail: CatalogNodeDetail | null | undefined): CatalogRelatedLinksFormValues {
  return {
    links: (detail?.related_links || []).map((link, index) => ({
      target_node_id: link.target_node_id,
      relation_type: link.relation_type === "generated_default" ? "manual" : link.relation_type === "default_override" ? "default_override" : "manual",
      hidden: Boolean(link.hidden),
      sort_order: link.sort_order || index + 1,
      label: link.label || "",
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
      links.push({
        target_node_id: targetNodeId,
        relation_type: link.relation_type || "manual",
        hidden: Boolean(link.hidden),
        sort_order: Number(link.sort_order || index + 1),
        label: link.label?.trim() || null,
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
    hybrid: "混合",
    shortcut: "快捷",
  };
  return labels[kind];
}

export function catalogStatusColor(status: string): string {
  if (status === "published") return "green";
  if (status === "archived") return "default";
  return "gold";
}
