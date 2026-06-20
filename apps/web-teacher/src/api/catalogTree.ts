import type { ApiList } from "./common";
import { api, postJson, putJson, patchJson } from "./http";
import type { MediaAsset } from "./media";

export type CatalogNodeKind = "directory" | "point";
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
  teacher_note?: string | null;
  student_description: string;
  card_image_asset_id?: string | null;
  card_icon_key?: string | null;
  card_accent?: string | null;
  card_layout: "default" | "compact" | "image" | "hero" | string;
  card_presentation: Record<string, unknown>;
  point_card_presentation: Record<string, unknown>;
  actions: string[];
  has_children: boolean;
  descendant_point_count: number;
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

export type CatalogPointJobStatus = "pending" | "running" | "succeeded" | "failed" | "disabled" | "unavailable";
export type CatalogPointEvidenceStatus = "missing" | "pending" | "running" | "succeeded" | "failed" | "stale" | "disabled" | "unavailable";
export type CatalogPointJobAction = "es-refresh" | "es-delete" | "rag-refresh" | "rag-delete" | "retry";

export type CatalogPointJob = {
  id: string;
  node_id: string;
  job_type: "es_upsert" | "es_delete" | "rag_evidence_refresh" | "rag_evidence_delete" | string;
  trigger_source: "automatic" | "manual" | "retry" | "system" | string;
  status: CatalogPointJobStatus;
  attempts: number;
  max_attempts: number;
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
  latest_error?: string | null;
  worker_id?: string | null;
  run_after?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CatalogPointEvidenceState = {
  node_id: string;
  evidence_status: CatalogPointEvidenceStatus;
  source_mode: string;
  trigger_policy: string;
  selected_chunk_ids: string[];
  source_refs: Array<Record<string, unknown>>;
  diagnostics: Record<string, unknown>;
  stale_reason?: string | null;
  latest_error?: string | null;
  refreshed_at?: string | null;
  stale_at?: string | null;
  last_attempted_at?: string | null;
  updated_at?: string | null;
};

export type CatalogPointJobState = {
  node_id: string;
  es_state?: CatalogIndexState | null;
  evidence_state: CatalogPointEvidenceState;
  recent_jobs: CatalogPointJob[];
};

export type CatalogStaticEvidenceBinding = {
  binding_id: string;
  chunk_id: string;
  evidence_role: string;
  selection_status: string;
  freshness_status: string;
  rank: number;
  score?: number | null;
  rerank_score?: number | null;
  source_title?: string | null;
  source_file?: string | null;
  document_id?: string | null;
  document_kind?: string | null;
  document_type?: string | null;
  page_number?: number | string | null;
  section_title?: string | null;
  chunk_index?: number | null;
  text_preview?: string | null;
  content_type?: string | null;
  source_metadata?: Record<string, unknown>;
  diagnostics?: Record<string, unknown>;
  updated_at?: string | null;
};

export type CatalogStaticEvidencePayload = {
  node_id: string;
  status: "missing_fallback_evidence" | "stale_fallback_evidence" | "available_static_fallback" | string;
  state: CatalogPointEvidenceState;
  bindings: CatalogStaticEvidenceBinding[];
  selected_chunk_ids: string[];
  binding_count: number;
  static_fallback_available: boolean;
  static_fallback_missing: boolean;
  dynamic_rag_primary: boolean;
  ai_consumable_without_static_binding: boolean;
  message: string;
};

export type CatalogPointAiContext = {
  teacher_only: true;
  node_id: string;
  point_title: string;
  catalog_path: CatalogBreadcrumb[];
  catalog_path_text: string;
  publication_state: Record<string, unknown>;
  student_facing_content: {
    principle_mode: CatalogPrincipleMode | string;
    principle_text?: string | null;
    principle_equation?: string | null;
    reaction_equations?: CatalogReactionEquationNormalized[];
    phenomenon_explanation?: string | null;
    safety_note?: string | null;
  };
  teacher_only_notes: {
    node_teacher_note?: string | null;
    point_teacher_note?: string | null;
  };
  related_points: CatalogRelatedLink[];
  videos: Array<Record<string, unknown>>;
  content_freshness: Record<string, unknown>;
  static_evidence: CatalogStaticEvidencePayload;
  dynamic_rag: {
    primary_path: boolean;
    probe_available: boolean;
    runtime_health: Record<string, unknown>;
    note: string;
  };
  job_state: CatalogPointJobState;
};

export type CatalogPointRagProbe = {
  ok: boolean;
  node_id: string;
  failed_stage?: string | null;
  reason?: string | null;
  runtime_health: Record<string, unknown>;
  generated_queries: string[];
  query_strategy: {
    status?: string;
    provider?: string;
    generated_queries?: string[];
    fields_used?: string[];
    fallback_reason?: string | null;
    field_policy?: string[];
  };
  recall_source?: string | null;
  candidate_counts: Record<string, number>;
  final_evidence: Array<Record<string, unknown>>;
  rerank_scores: Array<Record<string, unknown>>;
  fallbacks: Array<Record<string, unknown>>;
  trace: Record<string, unknown>;
};

export type CatalogReactionEquationInput = {
  raw_text: string;
  row_order?: number | null;
  label?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogReactionEquationNormalized = {
  id?: string | null;
  node_id?: string | null;
  row_order: number;
  raw_text: string;
  canonical_display: string;
  canonical_mhchem?: string | null;
  plain_search_text: string;
  formulae: string[];
  aliases: string[];
  reactants: string[];
  products: string[];
  participants: Record<string, unknown>;
  reaction_features: string[];
  validation_status: "valid" | "warning" | "invalid";
  warnings: string[];
  errors: string[];
  parser_version: string;
  migrated_from_principle_equation: boolean;
  metadata?: Record<string, unknown>;
};

export type CatalogEquationPreviewResponse = {
  ok: boolean;
  equations: CatalogReactionEquationNormalized[];
};

export type CatalogPointContent = {
  node_id: string;
  point_title: string;
  teacher_note?: string | null;
  principle_mode: CatalogPrincipleMode;
  principle_equation?: string | null;
  principle_text?: string | null;
  reaction_equations?: CatalogReactionEquationNormalized[];
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
  job_state?: CatalogPointJobState | null;
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
  teacher_note?: string | null;
  student_description?: string | null;
  card_image_asset_id?: string | null;
  card_icon_key?: string | null;
  card_accent?: string | null;
  card_layout?: string | null;
  card_presentation?: Record<string, unknown>;
  point_card_presentation?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

export type CatalogNodeUpdatePayload = {
  title?: string;
  summary?: string | null;
  node_kind?: CatalogNodeKind;
  teacher_note?: string | null;
  student_description?: string | null;
  card_image_asset_id?: string | null;
  card_icon_key?: string | null;
  card_accent?: string | null;
  card_layout?: string | null;
  card_presentation?: Record<string, unknown>;
  point_card_presentation?: Record<string, unknown>;
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
  reaction_equations?: CatalogReactionEquationInput[];
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

export function previewCatalogReactionEquations(equations: CatalogReactionEquationInput[]): Promise<CatalogEquationPreviewResponse> {
  return postJson<CatalogEquationPreviewResponse>("/api/admin/catalog/equations/preview", { equations });
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

export function getCatalogPointJobState(nodeId: string): Promise<CatalogPointJobState> {
  return api<CatalogPointJobState>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/job-state`);
}

export function triggerCatalogPointJob(nodeId: string, action: CatalogPointJobAction): Promise<CatalogPointJobState> {
  return postJson<CatalogPointJobState>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/jobs/${action}`, {});
}

export function getCatalogPointAiContext(nodeId: string): Promise<CatalogPointAiContext> {
  return api<CatalogPointAiContext>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/ai-context`);
}

export function runCatalogPointRagProbe(nodeId: string): Promise<CatalogPointRagProbe> {
  return postJson<CatalogPointRagProbe>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/rag-probe`, {});
}

export function searchCatalogNodes(query: string, chapterId?: string | null, limit = 80): Promise<CatalogSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (chapterId) params.set("chapter_id", chapterId);
  return api<CatalogSearchResponse>(`/api/admin/catalog/search?${params.toString()}`);
}

export function listCatalogCandidateMedia(limit = 200): Promise<ApiList<MediaAsset>> {
  return api<ApiList<MediaAsset>>(`/api/admin/media/assets?limit=${limit}`);
}
