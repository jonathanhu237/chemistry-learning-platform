import type { ApiList } from "./common";
import { api, postJson, putJson, patchJson } from "./http";
import type { MediaAsset } from "./media";

export type CatalogNodeKind = "directory" | "point";
export type CatalogNodeStatus = "draft" | "published" | "archived";
export type CatalogPrincipleMode = "equation" | "text";
export type CatalogMissingLearningFieldKey = "principle" | "phenomenon" | "safety";
export type CatalogNodePrimaryState =
  | "archived"
  | "blocked"
  | "needs_content"
  | "needs_video"
  | "draft"
  | "ready"
  | "published"
  | "sync_attention"
  | string;

export type CatalogValidation = {
  ok: boolean;
  errors: string[];
  warnings: string[];
  nodes?: Array<{ node_id: string; title: string; errors: string[]; warnings: string[] }>;
};

export type CatalogNodeStatusCondition = {
  key: string;
  group: "core_readiness" | "visibility" | "async_consumption" | "advanced" | string;
  severity: "error" | "warning" | "info" | "success" | string;
  status: string;
  reason: string;
  message: string;
  action?: string | null;
};

export type CatalogNodeStatusSummary = {
  primary_state: CatalogNodePrimaryState;
  primary_label?: string;
  primary_reason: string;
  core_readiness: {
    content_fields: "complete" | "missing" | "not_applicable" | string;
    video: "present" | "absent" | "not_applicable" | string;
    video_label?: string;
    missing_field_keys?: Array<CatalogMissingLearningFieldKey | string>;
    missing_field_labels?: string[];
    missing_fields?: string[];
    descendant_action_count?: number;
    descendant_status_counts?: Record<string, number>;
    descendant_missing_field_counts?: Record<CatalogMissingLearningFieldKey | string, number>;
  };
  visibility: {
    placement: CatalogNodeStatus | "missing" | "not_applicable" | string;
    shared_content: "missing" | "draft" | "published" | "archived" | "not_applicable" | string;
    student_available: boolean;
  };
  async_consumption: {
    search_index: "idle" | "pending" | "running" | "synced" | "stale" | "failed" | "disabled" | "unavailable" | "not_applicable" | string;
    ai_evidence: "idle" | "pending" | "running" | "available" | "stale" | "failed" | "disabled" | "unavailable" | "not_applicable" | string;
  };
  conditions: CatalogNodeStatusCondition[];
};

export type CatalogBreadcrumb = {
  node_id: string;
  title: string;
  node_kind: CatalogNodeKind;
  chapter_id: string;
};

export type CatalogNodeCard = {
  node_id: string;
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
  canonical_point_title?: string | null;
  canonical_point_status?: string | null;
  chapter_id: string;
  parent_id?: string | null;
  node_kind: CatalogNodeKind;
  title: string;
  summary: string;
  status: CatalogNodeStatus;
  display_order: number;
  teacher_note?: string | null;
  actions: string[];
  has_children: boolean;
  descendant_point_count: number;
  has_point_content: boolean;
  media_count: number;
  published_media_count: number;
  active_placement_count?: number;
  validation: CatalogValidation;
  node_status?: CatalogNodeStatusSummary | null;
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
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
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
  source_placement_node_id?: string | null;
  canonical_point_id?: string | null;
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
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
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
  canonical_point_id?: string | null;
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
  canonical_point_id?: string | null;
  row_order: number;
  raw_text: string;
  equation_core?: string;
  annotation_text?: string;
  annotation_formulae?: string[];
  annotation_aliases?: string[];
  condition_tags?: string[];
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
  suggested_display?: string | null;
  suggested_mhchem?: string | null;
  suggestion_reason?: string | null;
  corrections?: string[];
};

export type CatalogEquationPreviewResponse = {
  ok: boolean;
  equations: CatalogReactionEquationNormalized[];
};

export type CatalogEquationAssistDraft = {
  draft_text: string;
  source: string;
  rationale: string;
  row_order?: number | null;
  replacement_text?: string | null;
  canonical_display?: string;
  canonical_mhchem?: string | null;
  annotation_text?: string;
  annotation_formulae?: string[];
  condition_tags?: string[];
  validation_status?: "valid" | "warning" | "invalid";
  warnings?: string[];
  errors?: string[];
  formulae?: string[];
  supplemental?: boolean;
};

export type CatalogEquationAssistResponse = {
  available: boolean;
  reason?: string | null;
  drafts: CatalogEquationAssistDraft[];
};

export type CatalogPointContent = {
  node_id: string;
  canonical_point_id?: string | null;
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
  source_placement_node_id?: string | null;
  canonical_point_id?: string | null;
  media_id: string;
  title: string;
  binding_status: "draft" | "published" | "archived" | string;
  display_order: number;
  published_at?: string | null;
  metadata?: Record<string, unknown>;
  original_file_name: string;
  mime_type?: string | null;
  playback_mime_type?: string | null;
  source_file_size_bytes?: number | null;
  playback_file_size_bytes?: number | null;
  playback_width?: number | null;
  playback_height?: number | null;
  playback_duration_seconds?: number | null;
  playback_fps?: number | null;
  playback_bitrate?: number | null;
  playback_video_codec?: string | null;
  playback_audio_codec?: string | null;
  playback_rendition_kind?: string | null;
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
  source_canonical_point_id?: string | null;
  target_canonical_point_id?: string | null;
  target_placement_node_id?: string | null;
  target_title: string;
  relation_type: "manual" | "default_override" | "generated_default" | string;
  hidden: boolean;
  sort_order: number;
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
  canonical_point?: {
    canonical_point_id?: string | null;
    title?: string | null;
    status?: string | null;
    active_placement_count?: number;
  } | null;
  placements?: Array<CatalogNodeCard & { breadcrumbs?: CatalogBreadcrumb[] }>;
  breadcrumbs: CatalogBreadcrumb[];
  children: CatalogNodeCard[];
  point_content?: CatalogPointContent | null;
  media_bindings: CatalogMediaBinding[];
  related_links: CatalogRelatedLink[];
  validation: CatalogValidation;
  node_status?: CatalogNodeStatusSummary | null;
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

export type CatalogChapterTreeSummary = {
  chapter_id: string;
  node_count: number;
  directory_count: number;
  point_count: number;
  video_binding_count: number;
  playable_video_count: number;
  missing_video_count: number;
  actionable_point_count: number;
  point_status_counts: Record<string, number>;
  point_missing_field_counts?: Record<CatalogMissingLearningFieldKey | string, number>;
  directory_status_counts: Record<string, number>;
};

export type CatalogSearchResponse = {
  query: string;
  items: CatalogSearchResult[];
  meta?: CatalogSearchMeta;
};

export type CatalogSearchResult = CatalogNodeCard & {
  breadcrumbs?: CatalogBreadcrumb[];
  breadcrumb_path?: string;
  search_scope?: "current_chapter" | "other_chapter" | "all" | string | null;
  search_match?: {
    field_label?: string | null;
    backend?: "elasticsearch" | "postgres_fallback" | string;
    score?: number | null;
    primary_state?: string | null;
    catalog_path?: string[];
    search_scope?: "current_chapter" | "other_chapter" | "all" | string | null;
  } | null;
  stale_safe?: boolean;
};

export type CatalogSearchMeta = {
  backend: "elasticsearch" | "postgres_fallback" | "unavailable" | string;
  fallback_reason?: string | null;
  index?: string | null;
  mapping_version?: string | null;
  synonyms_active?: boolean;
  chemistry_recall_active?: boolean;
  status_filter?: string;
  chapter_id?: string | null;
  total?: number;
  returned?: number;
  stale_hit_count?: number;
  limited?: boolean;
  scope_counts?: Record<string, number>;
  scope_totals?: Record<string, number>;
  cross_chapter_enabled?: boolean;
};

export type CatalogPreviewTokenResponse = {
  preview_url: string;
  token: string;
  expires_at: string;
};

export type CatalogNodeCreatePayload = {
  chapter_id: string;
  parent_id?: string | null;
  after_node_id?: string | null;
  node_kind: CatalogNodeKind;
  title: string;
  summary?: string | null;
  teacher_note?: string | null;
  canonical_point_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogNodeUpdatePayload = {
  title?: string;
  summary?: string | null;
  node_kind?: CatalogNodeKind;
  teacher_note?: string | null;
  metadata?: Record<string, unknown>;
};

export type CatalogNodeMovePayload = {
  parent_id?: string | null;
  display_order?: number | null;
};

export type CatalogNodeCopyPayload = {
  chapter_id?: string | null;
  parent_id?: string | null;
  title?: string | null;
  include_subtree?: boolean;
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

export function getCatalogChapterTreeSummary(chapterId: string): Promise<CatalogChapterTreeSummary> {
  return api<CatalogChapterTreeSummary>(`/api/admin/catalog/chapters/${encodeURIComponent(chapterId)}/summary`);
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

export function copyCatalogNode(nodeId: string, payload: CatalogNodeCopyPayload): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/copy`, payload);
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

export function createCatalogPointPreviewToken(nodeId: string): Promise<CatalogPreviewTokenResponse> {
  return postJson<CatalogPreviewTokenResponse>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/preview-token`, {});
}

export function saveCatalogPointContent(nodeId: string, payload: CatalogPointContentPayload): Promise<CatalogNodeDetail> {
  return putJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/point-content`, payload);
}

export function previewCatalogReactionEquations(
  equations: CatalogReactionEquationInput[],
  multilineText?: string,
): Promise<CatalogEquationPreviewResponse> {
  return postJson<CatalogEquationPreviewResponse>("/api/admin/catalog/equations/preview", { equations, multiline_text: multilineText });
}

export function assistCatalogReactionEquations(payload: {
  mode: "suggest" | "fix" | "generate" | "balance";
  multiline_text?: string;
  equations?: CatalogReactionEquationInput[];
  point_title?: string;
  catalog_path_text?: string;
  phenomenon_explanation?: string;
  safety_note?: string;
}): Promise<CatalogEquationAssistResponse> {
  return postJson<CatalogEquationAssistResponse>("/api/admin/catalog/equations/assist", payload);
}

export function changeCatalogPointContentPublication(
  nodeId: string,
  action: "publish" | "unpublish" | "archive",
): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/point-content/publication`, { action });
}

export function bindCatalogPointMedia(
  nodeId: string,
  payload: { media_asset_id: string; title?: string | null; metadata?: Record<string, unknown> },
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

export function searchCatalogNodes(
  query: string,
  chapterId?: string | null,
  limit = 80,
  statusFilter = "all",
): Promise<CatalogSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  if (chapterId) params.set("chapter_id", chapterId);
  if (statusFilter && statusFilter !== "all") params.set("status_filter", statusFilter);
  return api<CatalogSearchResponse>(`/api/admin/catalog/search?${params.toString()}`);
}

export function listCatalogCandidateMedia(limit = 200): Promise<ApiList<MediaAsset>> {
  return api<ApiList<MediaAsset>>(`/api/admin/media/assets?limit=${limit}`);
}
