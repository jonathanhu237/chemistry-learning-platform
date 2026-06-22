import type { ApiList } from "./common";
import { api, postJson, postJsonStream } from "./http";
import type { Experiment } from "./experiments";
import type { AIConfiguration } from "./settings";
import type { LearningAssistantRuntime } from "./learningAssistant";

export type QuestionBankSummary = Experiment & {
  banks: Array<{
    id: string;
    experiment_id: string;
    bank_kind: string;
    title: string;
    status: string;
    source_label?: string | null;
    question_count: number;
    published_count: number;
    draft_count: number;
    choice_count?: number;
    true_false_count?: number;
    fill_blank_count?: number;
  }>;
};

export type SourceRef = {
  chunk_id?: string;
  source_file?: string;
  page_number?: number | string | null;
  section_title?: string | null;
  text?: string;
  [key: string]: unknown;
};

export type QuestionPoint = {
  point_node_id?: string;
  source_placement_node_id?: string;
  canonical_point_id?: string;
  point_key?: string;
  point_title?: string;
};

export type QuestionOptionLink = {
  label?: string;
  role?: string;
  point_node_id?: string;
  source_placement_node_id?: string;
  canonical_point_id?: string;
  point_key?: string;
  point_title?: string;
  diagnostic_note?: string;
  source_chunk_ids?: string[];
  [key: string]: unknown;
};

export type Question = {
  id: string;
  experiment_id: string;
  experiment_code?: string;
  experiment_title?: string;
  bank_kind?: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options: Array<{ label?: string; text?: string } | string>;
  answer: Record<string, unknown>;
  explanation?: string;
  difficulty?: string;
  status: string;
  related_chapter_ids?: string[];
  related_knowledge_point_ids?: string[];
  source_chunk_ids?: string[];
  source_refs?: SourceRef[];
  metadata?: {
    point_aware_question_bank?: boolean;
    suggestion_intent?: "add_questions" | "repair_question" | string;
    primary_point_node_ids?: string[];
    primary_canonical_point_ids?: string[];
    source_placement_node_ids?: string[];
    primary_point_keys?: string[];
    primary_points?: QuestionPoint[];
    secondary_point_node_ids?: string[];
    secondary_point_keys?: string[];
    option_links?: QuestionOptionLink[];
    coverage_tags?: string[];
    review_decision?: string;
    review_lineage?: Record<string, unknown>;
    quality_flags?: string[];
    mobile_input_risk?: string;
    machine_grading?: string;
    source_audit?: {
      evidence_sufficient?: boolean;
      evidence_contract?: string;
      evidence_source?: string;
      target_point_node_ids?: string[];
      target_canonical_point_ids?: string[];
      source_placement_node_ids?: string[];
      canonical_chunk_ids?: string[];
      supporting_theory_chunk_ids?: string[];
      reviewer_note?: string;
      model_reviewer_note?: string;
    };
    evidence_lineage?: {
      generation_id?: string | null;
      evidence_contract?: string;
      evidence_source?: string;
      target_point_node_ids?: string[];
      target_canonical_point_ids?: string[];
      source_placement_node_ids?: string[];
      source_ref_count?: number;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  created_at?: string;
  updated_at?: string;
};

export type QuestionBankChapterSummary = {
  chapter_id: string;
  chapter_number?: number | null;
  chapter_title: string;
  element_area?: string | null;
  total_count: number;
  choice_count: number;
  true_false_count: number;
  fill_blank_count: number;
  enabled_count: number;
  disabled_count: number;
  draft_count?: number;
  archived_count?: number;
  linked_experiment_count: number;
  updated_at?: string | null;
};

export type ChapterQuestion = Question & {
  chapter_ids?: string[];
  chapter_titles?: string[];
};

export type QuestionBankAssistantAction = {
  action_type: "add_question" | "repair_question" | "disable_question" | "coverage_report";
  title?: string;
  summary?: string;
  question_id?: string;
  question_type?: Question["question_type"];
  stem?: string;
  original_stem?: string;
  suggested_stem?: string;
  options?: Array<{ label?: string; text?: string } | string>;
  answer?: Record<string, unknown>;
  explanation?: string;
  counts?: Record<string, number>;
};

export type QuestionBankAssistantPreview = {
  proposal_id: string;
  intent: "add_questions" | "repair_question" | "coverage_check" | "disable_question";
  mode: string;
  mutates_bank: boolean;
  summary: string;
  warnings: string[];
  target: {
    chapter_id?: string | null;
    chapter_title?: string | null;
    experiment_id?: string | null;
    question_id?: string | null;
  };
  actions: QuestionBankAssistantAction[];
  source_refs: Array<Record<string, unknown>>;
};

export type QuestionDraft = {
  id: string;
  generation_id: string;
  experiment_id: string;
  experiment_code?: string;
  experiment_title?: string;
  payload: Partial<Question> & Record<string, unknown>;
  validation_errors: string[];
  status: string;
  prompt?: string;
  mode?: string;
  warning?: string;
  created_at?: string;
};

export type PointAwareSuggestionRequest = {
  intent: "add_questions" | "repair_question";
  experiment_id: string;
  prompt: string;
  question_id?: string | null;
  point_node_id?: string | null;
  point_node_ids?: string[];
  primary_canonical_point_ids?: string[];
  source_placement_node_ids?: string[];
  point_key?: string | null;
  point_keys?: string[];
  question_types?: Question["question_type"][];
  count?: number;
  difficulty?: string | null;
};

export type PointAwareSuggestionResponse = {
  generation_id: string;
  mode: string;
  warning?: string;
  source_refs: SourceRef[];
  drafts: QuestionDraft[];
  target: {
    intent: "add_questions" | "repair_question";
    experiment_id: string;
    question_id?: string | null;
    point?: QuestionPoint | null;
  };
};

export type QuestionWorkbenchTurn = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  provider?: string | null;
  model?: string | null;
  error_state?: Record<string, unknown> | null;
  metadata?: Record<string, unknown>;
  created_at?: string;
};

export type QuestionWorkbenchCandidate = {
  id: string;
  session_id: string;
  turn_id?: string | null;
  draft_id?: string | null;
  payload: Partial<Question> & Record<string, unknown>;
  validation_errors: string[];
  status: "draft" | "rejected" | "published";
  lineage?: Record<string, unknown>;
  draft_status?: string | null;
  draft_validation_errors?: string[] | null;
  created_at?: string;
  updated_at?: string;
};

export type QuestionWorkbenchSession = {
  id: string;
  mode: "repair" | "create";
  experiment_id: string;
  experiment_code?: string;
  experiment_title?: string;
  point_node_id?: string | null;
  source_placement_node_id?: string | null;
  canonical_point_id?: string | null;
  point_key?: string | null;
  question_id?: string | null;
  original_question_snapshot?: Partial<Question> & Record<string, unknown>;
  context_snapshot?: {
    experiment?: {
      id?: string;
      code?: string;
      title?: string;
      summary?: string | null;
    };
    selected_point?: QuestionPoint | null;
    target_points?: QuestionPoint[];
    target_point_node_ids?: string[];
    target_canonical_point_ids?: string[];
    source_placement_node_ids?: string[];
    target_point_keys?: string[];
    catalog_point_contexts?: Array<Record<string, unknown>>;
    source_refs?: SourceRef[];
    rag_gate?: {
      healthy?: boolean;
      status?: string;
      reason_code?: string;
      message?: string;
      rag_runtime?: AIConfiguration["rag_runtime"];
      bge_status?: LearningAssistantRuntime["bge_status"];
      bge_error?: string | null;
      bge_metrics?: LearningAssistantRuntime["bge_metrics"];
      [key: string]: unknown;
    };
    evidence_package?: {
      mode?: string;
      source_refs?: SourceRef[];
      source_count?: number;
      diagnostics?: Record<string, unknown>;
      [key: string]: unknown;
    };
    coverage?: {
      question_count?: number;
      selected_point_question_count?: number | null;
      type_counts?: Record<string, number>;
    };
    last_prompt?: string;
    [key: string]: unknown;
  };
  status: "open" | "closed" | "discarded";
  turns: QuestionWorkbenchTurn[];
  candidates: QuestionWorkbenchCandidate[];
  created_at?: string;
  updated_at?: string;
};

export type QuestionRegenerationAudit = {
  catalog_point_count: number;
  covered_point_count: number;
  unresolved_point_count: number;
  question_type_counts: Record<string, number>;
  draft_question_type_counts: Record<string, number>;
  evidence_source_counts: Record<string, number>;
  draft_status_counts: Record<string, number>;
  workbench_candidate_status_counts: Record<string, number>;
  accepted_draft_count: number;
  rejected_draft_count: number;
  by_chapter: Array<Record<string, unknown>>;
  by_directory: Array<Record<string, unknown>>;
  by_point: Array<Record<string, unknown>>;
  unresolved_points: Array<Record<string, unknown>>;
};

export type QuestionBankBaseline = {
  question_bank_empty: boolean;
  retired_legacy_seed: boolean;
  message?: string;
  requires_catalog_node_evidence: boolean;
  regeneration_audit?: QuestionRegenerationAudit;
};

export type QuestionBankListResponse = ApiList<QuestionBankSummary> & {
  baseline?: QuestionBankBaseline;
  regeneration_audit?: QuestionRegenerationAudit;
};

export function listQuestionBanks(): Promise<QuestionBankListResponse> {
  return api<QuestionBankListResponse>("/api/admin/question-banks");
}

export function listQuestionBankQuestions(params: URLSearchParams): Promise<ApiList<Question>> {
  return api<ApiList<Question>>(`/api/admin/question-banks/questions?${params.toString()}`);
}

export function listQuestionDrafts(experimentId: string): Promise<ApiList<QuestionDraft>> {
  return api<ApiList<QuestionDraft>>(`/api/admin/question-banks/drafts?experiment_id=${experimentId}`);
}

export function getQuestionWorkbenchSession(sessionId: string): Promise<QuestionWorkbenchSession> {
  return api<QuestionWorkbenchSession>(`/api/admin/question-banks/workbench-sessions/${sessionId}`);
}

export function createQuestionWorkbenchSession(payload: unknown): Promise<QuestionWorkbenchSession> {
  return postJson<QuestionWorkbenchSession>("/api/admin/question-banks/workbench-sessions", payload);
}

export function streamQuestionWorkbench<T>(path: string, body: unknown, onEvent: Parameters<typeof postJsonStream<T>>[2]): Promise<void> {
  return postJsonStream<T>(path, body, onEvent);
}

export function publishQuestionWorkbenchCandidate(candidateId: string): Promise<Question> {
  return postJson<Question>(`/api/admin/question-banks/workbench-candidates/${candidateId}/publish`, {});
}

export function rejectQuestionWorkbenchCandidate(candidateId: string): Promise<QuestionWorkbenchCandidate> {
  return postJson<QuestionWorkbenchCandidate>(`/api/admin/question-banks/workbench-candidates/${candidateId}/reject`, {});
}
