import type { ApiList } from "./common";
import { api, postJson, putJson, patchJson } from "./http";
import type { MediaAsset } from "./media";

export type CatalogNodeKind = "directory" | "point" | "hybrid" | "shortcut";
export type CatalogNodeStatus = "draft" | "published" | "archived";
export type CatalogPrincipleMode = "equation" | "text";

export type CatalogValidation = {
  ok: boolean;
  errors: string[];
  warnings: string[];
  nodes?: Array<{ node_id: string; title: string; errors: string[]; warnings: string[] }>;
};

export type CatalogBreadcrumb = {
  node_id: string;
  title: string;
  node_kind: CatalogNodeKind;
  chapter_id: string;
};

export type CatalogNodeCard = {
  node_id: string;
  chapter_id: string;
  parent_id?: string | null;
  node_kind: CatalogNodeKind;
  title: string;
  summary: string;
  status: CatalogNodeStatus;
  display_order: number;
  shortcut_target_node_id?: string | null;
  actions: string[];
  has_children: boolean;
  has_point_content: boolean;
  media_count: number;
  published_media_count: number;
  validation: CatalogValidation;
  index_state?: CatalogIndexState | null;
};

export type CatalogIndexState = {
  document_id: string;
  desired_action: "upsert" | "delete";
  sync_status: "pending" | "synced" | "failed" | "disabled";
  attempts: number;
  last_error?: string | null;
  indexed_at?: string | null;
  updated_at?: string | null;
};

export type CatalogPointContent = {
  node_id: string;
  point_title: string;
  teacher_note?: string | null;
  principle_mode: CatalogPrincipleMode;
  principle_equation?: string | null;
  principle_text?: string | null;
  phenomenon_explanation?: string | null;
  safety_note?: string | null;
  content_status: "missing" | "draft" | "published" | "archived";
  published_at?: string | null;
  updated_at?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogMediaBinding = {
  binding_id: string;
  node_id: string;
  media_id: string;
  title: string;
  binding_status: "draft" | "published" | "archived" | string;
  display_order: number;
  published_at?: string | null;
  metadata?: Record<string, unknown>;
  original_file_name: string;
  mime_type?: string | null;
  playback_mime_type?: string | null;
  upload_status: string;
  processing_phase?: string | null;
  processing_progress?: number | null;
  error_reason?: string | null;
  has_thumbnail?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type CatalogRelatedLink = {
  id?: string | null;
  source_node_id: string;
  target_node_id: string;
  target_title: string;
  relation_type: "manual" | "default_override" | "generated_default" | string;
  hidden: boolean;
  sort_order: number;
  label?: string | null;
  source: "manual" | "generated_default" | string;
  metadata?: Record<string, unknown>;
};

export type CatalogSearchPreview = {
  id?: string;
  node_id?: string;
  title?: string;
  summary?: string;
  catalog_path?: string[];
  principle_text?: string;
  phenomenon_explanation?: string;
  safety_note?: string;
  related_points?: Array<{ node_id: string; title: string }>;
  videos?: Array<{ media_id: string; title: string }>;
  [key: string]: unknown;
};

export type CatalogNodeDetail = {
  node: CatalogNodeCard;
  breadcrumbs: CatalogBreadcrumb[];
  children: CatalogNodeCard[];
  point_content?: CatalogPointContent | null;
  media_bindings: CatalogMediaBinding[];
  related_links: CatalogRelatedLink[];
  validation: CatalogValidation;
  search_preview?: CatalogSearchPreview | null;
  index_state?: CatalogIndexState | null;
};

export type CatalogRootsResponse = {
  chapter: { chapter_id: string; chapter_title: string };
  nodes: CatalogNodeCard[];
};

export type CatalogChildrenResponse = {
  parent: CatalogNodeCard;
  children: CatalogNodeCard[];
};

export type CatalogSearchResponse = {
  query: string;
  items: CatalogNodeCard[];
};

export type CatalogNodeCreatePayload = {
  chapter_id: string;
  parent_id?: string | null;
  after_node_id?: string | null;
  node_kind: CatalogNodeKind;
  title: string;
  summary?: string | null;
  shortcut_target_node_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogNodeUpdatePayload = {
  title?: string;
  summary?: string | null;
  node_kind?: CatalogNodeKind;
  shortcut_target_node_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogNodeMovePayload = {
  parent_id?: string | null;
  display_order?: number | null;
};

export type CatalogPointContentPayload = {
  point_title: string;
  teacher_note?: string | null;
  principle_mode: CatalogPrincipleMode;
  principle_equation?: string | null;
  principle_text?: string | null;
  phenomenon_explanation?: string | null;
  safety_note?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogRelatedLinksPayload = {
  links: Array<{
    target_node_id: string;
    relation_type: "manual" | "default_override" | "generated_default";
    hidden: boolean;
    sort_order: number;
    label?: string | null;
    metadata?: Record<string, unknown>;
  }>;
};

export function listCatalogRoots(chapterId: string, includeArchived = false): Promise<CatalogRootsResponse> {
  const suffix = includeArchived ? "?include_archived=true" : "";
  return api<CatalogRootsResponse>(`/api/admin/catalog/chapters/${encodeURIComponent(chapterId)}/roots${suffix}`);
}

export function listCatalogChildren(nodeId: string, includeArchived = false): Promise<CatalogChildrenResponse> {
  const suffix = includeArchived ? "?include_archived=true" : "";
  return api<CatalogChildrenResponse>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/children${suffix}`);
}

export function getCatalogNode(nodeId: string): Promise<CatalogNodeDetail> {
  return api<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}`);
}

export function createCatalogNode(payload: CatalogNodeCreatePayload): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>("/api/admin/catalog/nodes", payload);
}

export function updateCatalogNode(nodeId: string, payload: CatalogNodeUpdatePayload): Promise<CatalogNodeDetail> {
  return patchJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}`, payload);
}

export function moveCatalogNode(nodeId: string, payload: CatalogNodeMovePayload): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/move`, payload);
}

export function reorderCatalogNodes(items: Array<{ node_id: string; display_order: number }>): Promise<{ updated: number }> {
  return postJson<{ updated: number }>("/api/admin/catalog/nodes/reorder", { items });
}

export function changeCatalogNodeStatus(
  nodeId: string,
  payload: { action: "archive" | "restore" | "publish" | "unpublish"; include_subtree?: boolean },
): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/status`, payload);
}

export function saveCatalogPointContent(nodeId: string, payload: CatalogPointContentPayload): Promise<CatalogNodeDetail> {
  return putJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/point-content`, payload);
}

export function changeCatalogPointContentPublication(
  nodeId: string,
  action: "publish" | "unpublish" | "archive",
): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/point-content/publication`, { action });
}

export function bindCatalogPointMedia(
  nodeId: string,
  payload: { media_asset_id: string; title?: string | null; status: "draft" | "published"; metadata?: Record<string, unknown> },
): Promise<{ binding_id: string; detail: CatalogNodeDetail }> {
  return postJson(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/media-bindings`, payload);
}

export function uploadCatalogPointMedia(nodeId: string, title: string, file: File): Promise<{ asset: MediaAsset; detail: CatalogNodeDetail }> {
  const body = new FormData();
  body.append("title", title);
  body.append("file", file);
  return api(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/media/upload`, { method: "POST", body });
}

export function changeCatalogMediaBindingStatus(bindingId: string, action: "publish" | "unpublish" | "delete"): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/media-bindings/${encodeURIComponent(bindingId)}/${action}`, {});
}

export function saveCatalogRelatedLinks(nodeId: string, payload: CatalogRelatedLinksPayload): Promise<CatalogNodeDetail> {
  return putJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/related-links`, payload);
}

export function validateCatalogNode(nodeId: string, includeSubtree = false): Promise<CatalogValidation> {
  const suffix = includeSubtree ? "?include_subtree=true" : "";
  return api<CatalogValidation>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/validation${suffix}`);
}

export function searchCatalogNodes(query: string, chapterId?: string | null, limit = 80): Promise<CatalogSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (chapterId) params.set("chapter_id", chapterId);
  return api<CatalogSearchResponse>(`/api/admin/catalog/search?${params.toString()}`);
}

export function listCatalogCandidateMedia(limit = 200): Promise<ApiList<MediaAsset>> {
  return api<ApiList<MediaAsset>>(`/api/admin/media/assets?limit=${limit}`);
}
