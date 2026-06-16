export type User = {
  id: string;
  username: string;
  role: "admin" | "teacher" | "student";
  display_name: string;
  status: string;
  must_change_password?: boolean;
};

export type ClassItem = {
  id: string;
  class_name: string;
  description?: string | null;
  status: string;
  student_count: number;
};

export type RosterStudent = {
  id: string;
  class_id: string;
  student_id: string;
  student_name: string;
  status: "pending" | "active" | "disabled";
  activation_mode: "default_password" | "self_registration";
  activated: boolean;
  user_id?: string | null;
  activated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type RosterImportResult = {
  import_id: string;
  mode: "upsert" | "overwrite";
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  disabled_missing: number;
};

export type RegistrationSettings = {
  mode: "roster_only" | "self_registration";
  default_password_policy: string;
  default_password_mode: "student_id" | "shared";
  has_default_password: boolean;
  source?: "system_default" | "class" | null;
};

export type LearningBehaviorSettings = {
  assessment: {
    pretest_enabled: boolean;
    pretest_question_count: number;
    posttest_enabled: boolean;
    posttest_question_count: number;
  };
  learning_features: {
    ai_assistant_enabled: boolean;
    feedback_enabled: boolean;
    student_review_preview_enabled: boolean;
  };
};

export type PlatformSettingsResponse = {
  settings: LearningBehaviorSettings;
  can_edit: boolean;
};

export type FeedbackStatus = "open" | "in_progress" | "resolved" | "archived";

export type FeedbackType = "course_content" | "experiment_resource" | "ai_answer" | "system_issue" | "other";

export type FeedbackItem = {
  id: string;
  student_id: string;
  class_id?: string | null;
  student_name_snapshot?: string | null;
  class_name_snapshot?: string | null;
  feedback_type: FeedbackType;
  content: string;
  status: FeedbackStatus;
  chapter_id?: string | null;
  unit_id?: string | null;
  knowledge_point_id?: string | null;
  experiment_id?: string | null;
  page_path?: string | null;
  source_event_id?: number | null;
  handler_user_id?: string | null;
  handler_display_name?: string | null;
  internal_note?: string | null;
  metadata?: Record<string, unknown>;
  resolved_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type FeedbackSummary = {
  total_count: number;
  open_count: number;
  in_progress_count: number;
  resolved_count: number;
  archived_count: number;
  recent_count: number;
};

export type FeedbackListResponse = ApiList<FeedbackItem>;

export type FeedbackUpdate = {
  status?: FeedbackStatus;
  internal_note?: string | null;
};

export type AIConfiguration = {
  provider: "openai";
  base_url: string;
  model: string;
  connection_check_interval_minutes: number;
  api_key_configured: boolean;
  api_key_fingerprint?: string | null;
  enabled_features: {
    rag_access_enabled: boolean;
    student_ai_assistant: boolean;
    student_learning_analytics: boolean;
    question_bank_assistant: boolean;
    teacher_learning_analytics: boolean;
  };
  status: {
    ready: boolean;
    message: string;
    effective_mode: string;
    connectivity_status: "not_configured" | "untested" | "connected" | "failed" | "stale";
    last_checked_at?: string | null;
    last_check_message?: string | null;
    check_interval_minutes: number;
    next_check_due_at?: string | null;
    recent_request_count: number;
    recent_error_count: number;
    last_request_at?: string | null;
    last_error_at?: string | null;
    usage_buckets: Array<{
      bucket: string;
      request_count: number;
      error_count: number;
    }>;
    usage_trends: Partial<Record<
      "1d" | "7d" | "30d",
      {
        range: "1d" | "7d" | "30d";
        bucket_unit: "hour" | "half_day" | "day";
        buckets: Array<{
          bucket: string;
          request_count: number;
          error_count: number;
        }>;
      }
    >>;
    last_request_summary?: {
      called_at: string;
      channel: string;
      status: "success" | "error";
    } | null;
  };
  student_ai_policy: {
    active: boolean;
    version: string;
    model: string;
    coverage: string[];
    recent_decision_count: number;
    invalid_decision_count: number;
    outcomes: Array<{
      mode: string;
      label: string;
      count: number;
    }>;
  };
  rag_runtime?: {
    rag_enabled: boolean;
    hybrid_bge_enabled: boolean;
    bge_service_required: boolean;
    bge_service_url: string;
    query_generation_enabled: boolean;
    vector_top_k: number;
    rerank_top_k: number;
    final_top_k: number;
    status: string;
    message: string;
  };
  can_edit: boolean;
};

export type AIConfigurationUpdate = {
  provider: "openai";
  base_url: string;
  model: string;
  connection_check_interval_minutes: number;
  api_key?: string | null;
  enabled_features: AIConfiguration["enabled_features"];
};

export type LearningAssistantAskRequest = {
  question: string;
  student_id?: string | null;
  chapter_id?: string | null;
  experiment_id?: string | null;
  point_key?: string | null;
  knowledge_point_ids?: string[];
  allow_progress_lookup: boolean;
  allow_rag_lookup: boolean;
  conversation_history?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  max_answer_chars?: number | null;
};

export type LearningAssistantSourceAsset = {
  path: string;
  file_name: string;
  kind: "figure" | "page" | string;
  caption?: string | null;
};

export type LearningAssistantSource = {
  chunk_id: string;
  source_file?: string | null;
  page_number?: number | null;
  text_preview: string;
  content_type?: string | null;
  caption?: string | null;
  section_path?: string[];
  assets?: LearningAssistantSourceAsset[];
};

export type LearningAssistantResponse = {
  answer: string;
  sources: LearningAssistantSource[];
  mode: string;
  classification: Record<string, unknown>;
  tool_calls: Array<Record<string, unknown>>;
  guardrail_decisions: Array<{
    code?: string;
    action?: string;
    reason?: string;
    [key: string]: unknown;
  }>;
  rag_trace?: Record<string, unknown>;
  review_required: boolean;
};

export type LearningAssistantRuntime = {
  checked_at: string;
  rag_runtime?: AIConfiguration["rag_runtime"];
  bge_status?: "not_required" | "checking" | "healthy" | "degraded" | "unreachable" | "not_configured" | string;
  bge_error?: string | null;
  bge_metrics?: {
    ok?: boolean;
    service?: string;
    request_ms?: number;
    config?: {
      embed_model?: string;
      rerank_model?: string;
      device?: string;
      use_fp16?: boolean;
      rerank_backend?: string;
      rerank_max_length?: number;
      offline?: boolean;
      [key: string]: unknown;
    };
    models?: {
      embed_loaded?: boolean;
      rerank_loaded?: boolean;
      [key: string]: unknown;
    };
    requests?: {
      embed?: number;
      rerank?: number;
      [key: string]: unknown;
    };
    process?: {
      uptime_seconds?: number;
      cpu_user_seconds?: number;
      cpu_system_seconds?: number;
      memory_rss_mb?: number | null;
      memory_high_water_mb?: number | null;
      thread_count?: number | null;
      [key: string]: unknown;
    };
    container?: {
      memory_current_mb?: number | null;
      memory_limit_mb?: number | null;
      cpu_usage_seconds?: number | null;
      cpu_user_seconds?: number | null;
      cpu_system_seconds?: number | null;
      cpu_throttled_seconds?: number | null;
      [key: string]: unknown;
    };
    warmup?: {
      enabled?: boolean;
      status?: "disabled" | "not_started" | "running" | "succeeded" | "failed" | string;
      trigger?: string | null;
      started_at?: string | null;
      finished_at?: string | null;
      duration_ms?: number | null;
      error?: string | null;
      models_ready?: boolean;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  } | null;
};

export type Chapter = {
  chapter_id: string;
  area_id?: string | null;
  chapter_number?: number;
  chapter_title: string;
  element_area?: string | null;
  knowledge_point_count?: number;
  visible_experiment_count?: number;
  question_count?: number;
};

export type LearningResourceKnowledgePoint = {
  knowledge_point_id: string;
  content: string;
};

export type LearningResourceUnit = {
  unit_id: string;
  unit_index?: number | null;
  unit_title: string;
  knowledge_point_count: number;
  knowledge_points: LearningResourceKnowledgePoint[];
};

export type ResourceCountMap = Record<string, number>;

export type LearningResourceExperiment = {
  id: string;
  code?: string;
  title: string;
  status: string;
  display_order?: number | null;
  media_count: number;
  media_ready_count?: number;
  media_published_count?: number;
  media_asset_status_counts?: ResourceCountMap;
  media_binding_status_counts?: ResourceCountMap;
  question_count: number;
  question_status_counts?: ResourceCountMap;
  question_type_counts?: ResourceCountMap;
};

export type LearningResourceGroup = {
  id: string;
  kind: "chapter" | "general";
  chapter_id: string;
  chapter_number?: number | null;
  title: string;
  subtitle?: string | null;
  area_id: string;
  area_name: string;
  knowledge_unit_count: number;
  knowledge_point_count: number;
  experiment_count: number;
  question_count: number;
  question_status_counts?: ResourceCountMap;
  question_type_counts?: ResourceCountMap;
  media_count: number;
  media_ready_count?: number;
  media_published_count?: number;
  media_asset_status_counts?: ResourceCountMap;
  media_binding_status_counts?: ResourceCountMap;
  units: LearningResourceUnit[];
  experiments: LearningResourceExperiment[];
};

export type LearningResourceArea = {
  area_id: string;
  area_name: string;
  kind: "theory" | "general";
  group_ids: string[];
  metrics: {
    group_count: number;
    knowledge_unit_count: number;
    knowledge_point_count: number;
    experiment_count: number;
    question_count: number;
    media_count: number;
    media_ready_count?: number;
    media_published_count?: number;
  };
};

export type ExperimentFrameworkNode = {
  id: string;
  parent_id?: string | null;
  source_collection: string;
  doc_id: string;
  book_title: string;
  node_type: "book" | "chapter" | "section" | "protocol";
  title: string;
  full_path: string[];
  depth: number;
  display_order: number;
  page_start?: number | null;
  page_end?: number | null;
  metadata?: Record<string, unknown>;
  content_status?: string;
  direct_evidence_count: number;
  evidence_count: number;
  direct_formal_experiment_count: number;
  formal_experiment_count: number;
  child_count: number;
  video_count: number;
  published_video_count: number;
  question_count: number;
  published_question_count: number;
};

export type ExperimentFrameworkFormalLink = {
  node_id: string;
  experiment_id: string;
  experiment_code?: string | null;
  experiment_title: string;
  experiment_status: string;
  relation_type: "formal_parent_title" | "canonical_evidence";
  link_source?: string | null;
  evidence_chunk_id?: string | null;
  evidence_section_title?: string | null;
  confidence?: number | string | null;
  sort_order?: number | null;
};

export type ExperimentKnowledgeFrameworkOverview = {
  available: boolean;
  source: {
    source_collection: string;
    doc_id: string;
    book_title: string;
  };
  metrics: {
    node_count: number;
    chapter_count: number;
    section_count: number;
    protocol_count: number;
    canonical_chunk_count: number;
    linked_chunk_count: number;
    formal_experiment_count: number;
    formal_link_count: number;
    canonical_evidence_link_count: number;
    video_count: number;
    published_video_count: number;
    question_count: number;
    published_question_count: number;
  };
  roots: ExperimentFrameworkNode[];
  nodes: ExperimentFrameworkNode[];
  formal_links: ExperimentFrameworkFormalLink[];
};

export type LearningResourceOverview = {
  metrics: {
    knowledge_unit_count: number;
    knowledge_point_count: number;
    experiment_count: number;
    media_resource_count: number;
    question_count: number;
    published_question_count?: number;
    draft_question_count?: number;
    published_video_binding_count?: number;
    video_asset_count?: number;
    class_count?: number;
    student_count?: number;
  };
  domains?: {
    knowledge?: {
      title?: string;
      knowledge_unit_count: number;
      knowledge_point_count: number;
      source_document_count: number;
      source_chunk_count: number;
      embedding_count: number;
    };
    experiment_video?: {
      title?: string;
      experiment_count: number;
      experiment_status_counts?: ResourceCountMap;
      video_asset_count: number;
      video_binding_count: number;
      ready_video_count: number;
      published_video_count: number;
      asset_status_counts?: ResourceCountMap;
      binding_status_counts?: ResourceCountMap;
    };
    question_bank?: {
      title?: string;
      question_count: number;
      status_counts?: ResourceCountMap;
      type_counts?: ResourceCountMap;
      published_question_count: number;
      draft_question_count: number;
    };
    classes_students?: {
      title?: string;
      class_count: number;
      class_status_counts?: ResourceCountMap;
      roster_count: number;
      roster_status_counts?: ResourceCountMap;
      student_account_count: number;
      student_status_counts?: ResourceCountMap;
      active_student_count: number;
    };
  };
  areas: LearningResourceArea[];
  groups: LearningResourceGroup[];
  experiment_framework?: ExperimentKnowledgeFrameworkOverview | null;
};

export type ChapterBinding = {
  chapter_id: string;
  chapter_title?: string;
  chapter_number?: number;
  coverage_type: "primary" | "partial" | "supporting";
  notes?: string | null;
  sort_order?: number;
};

export type MediaResource = {
  binding_id?: string;
  media_id?: string;
  title?: string;
  original_file_name?: string;
  mime_type?: string;
  file_size_bytes?: number;
  thumbnail_relative_path?: string | null;
  upload_status?: string;
  binding_status?: string;
  point_key?: string | null;
  point_title?: string | null;
  published_at?: string;
};

export type Experiment = {
  id: string;
  code: string;
  title: string;
  title_en?: string;
  summary?: string;
  metadata?: Record<string, unknown>;
  status: "draft" | "published" | "archived";
  display_order: number;
  chapter_bindings: ChapterBinding[];
  media_resources: MediaResource[];
  published_question_count: number;
  draft_question_count: number;
  generated_draft_count: number;
};

export type MediaAsset = {
  id: string;
  title: string;
  original_file_name: string;
  relative_path?: string;
  source_relative_path?: string | null;
  thumbnail_relative_path?: string | null;
  playback_relative_path?: string | null;
  playback_mime_type?: string | null;
  checksum_sha256?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  bitrate?: number | null;
  video_codec?: string | null;
  audio_codec?: string | null;
  upload_status: string;
  processing_phase?: string | null;
  processing_progress?: number | null;
  error_reason?: string | null;
  created_at?: string;
  updated_at?: string;
  association_count?: number;
  processing_job?: MediaProcessingJob | null;
  renditions?: MediaRendition[];
  duplicate_candidates?: MediaDuplicateCandidate[];
};

export type MediaProcessingJob = {
  id: string;
  status: string;
  phase?: string | null;
  progress?: number | null;
  attempts?: number | null;
  error_reason?: string | null;
  updated_at?: string | null;
};

export type MediaRendition = {
  id?: string;
  kind: string;
  relative_path?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  status?: string | null;
  video_codec?: string | null;
  audio_codec?: string | null;
};

export type MediaDuplicateCandidate = {
  id: string;
  duplicate_type: "exact" | "suspected";
  score?: number | null;
  algorithm: string;
  status: "pending" | "kept" | "reused" | "ignored";
  candidate_asset_id?: string | null;
  candidate_title?: string | null;
  candidate_thumbnail_relative_path?: string | null;
};

export type MediaDuplicatePrecheck = {
  exists: boolean;
  asset?: MediaAsset | null;
};

export type ExperimentVideoPointResource = {
  binding_id: string;
  experiment_id: string;
  experiment_title?: string;
  binding_title?: string | null;
  binding_status: string;
  point_key?: string | null;
  point_title?: string | null;
  media_id: string;
  media_title: string;
  title?: string;
  original_file_name: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  thumbnail_relative_path?: string | null;
  upload_status: string;
  error_reason?: string | null;
  published_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type ExperimentVideoPoint = {
  point_key: string;
  point_title: string;
  source: "candidate" | "stored" | "legacy";
  resources: ExperimentVideoPointResource[];
  resource_count: number;
  published_count: number;
};

export type ExperimentVideoPointsResponse = {
  experiment: {
    id: string;
    code: string;
    title: string;
    status: Experiment["status"];
  };
  points: ExperimentVideoPoint[];
  total_points: number;
  total_resources: number;
  published_resources: number;
};

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
  point_key?: string;
  point_title?: string;
};

export type QuestionOptionLink = {
  label?: string;
  role?: string;
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
    primary_point_keys?: string[];
    primary_points?: QuestionPoint[];
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
      canonical_chunk_ids?: string[];
      supporting_theory_chunk_ids?: string[];
      reviewer_note?: string;
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
    target_point_keys?: string[];
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

export type AnalyticsDashboard = {
  class_id: string;
  metrics: {
    class_size: number;
    active_students: number;
    published_experiments: number;
    completion_rate: number;
    average_score: number;
    missing_students: number;
  };
  experiments: Experiment[];
  matrix: Array<{
    student_id: string;
    student_name: string;
    status?: string;
    experiments: Record<
      string,
      {
        status: string;
        completion_percent: number;
        best_score: number | null;
        attempt_count: number;
      }
    >;
  }>;
  recent_activity: Array<Record<string, unknown>>;
  missing_students: Array<Record<string, unknown>>;
};

export type WeakQuestionItem = {
  experiment_id?: string;
  experiment_code?: string;
  experiment_title?: string;
  question_id?: string;
  stem?: string;
  attempt_count: number;
  incorrect_count: number;
  incorrect_rate: number;
  weak_kp_ids?: string[];
  unmapped?: boolean;
};

export type WeakVideoPointItem = {
  point_key: string;
  point_title: string;
  experiment_id?: string;
  experiment_code?: string;
  experiment_title?: string;
  attempt_count: number;
  incorrect_count: number;
  incorrect_rate: number;
  representative_questions?: Array<{ question_id?: string; stem?: string }>;
  selected_option_links?: QuestionOptionLink[];
  kp_unmapped?: boolean;
};

export type WeakPointsResponse = ApiList<WeakQuestionItem> & {
  point_items: WeakVideoPointItem[];
  point_total: number;
};

export type StudentAttempt = {
  id?: string;
  experiment_id?: string;
  experiment_code?: string;
  experiment_title?: string;
  question_id?: string;
  question_type?: Question["question_type"];
  stem?: string;
  correct?: boolean | null;
  score?: number | null;
  submitted_answer?: unknown;
  answer?: unknown;
  metadata?: {
    primary_points?: QuestionPoint[];
    primary_point_keys?: string[];
    selected_option_label?: string | null;
    selected_option_link?: QuestionOptionLink | null;
    diagnostic_role?: string | null;
    [key: string]: unknown;
  };
  created_at?: string;
};

export type StudentReport = {
  student?: Record<string, unknown>;
  progress?: Array<Record<string, unknown>>;
  attempts?: StudentAttempt[];
  weak_points?: Array<Record<string, unknown>>;
  weak_video_points?: WeakVideoPointItem[];
  timeline?: Array<Record<string, unknown>>;
};

export type ApiList<T> = {
  items: T[];
  total: number;
};

export const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

let authToken = localStorage.getItem("chem_admin_token") || "";

export function getAuthToken(): string {
  return authToken;
}

export function setAuthToken(token: string): void {
  authToken = token;
  if (token) {
    localStorage.setItem("chem_admin_token", token);
  } else {
    localStorage.removeItem("chem_admin_token");
  }
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (response.status === 401) {
    setAuthToken("");
  }
  if (!response.ok) {
    throw new ApiError(response.status, typeof payload === "object" && payload ? payload.detail : payload);
  }
  return payload as T;
}

export type JsonStreamEvent<T = unknown> = {
  event: string;
  data: T;
};

function parseSseBlock(raw: string): JsonStreamEvent | null {
  const lines = raw.split(/\r?\n/);
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim() || "message";
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }
  if (!dataLines.length) return null;
  const dataText = dataLines.join("\n");
  try {
    return { event, data: JSON.parse(dataText) };
  } catch {
    return { event, data: dataText };
  }
}

export async function postJsonStream<T>(
  path: string,
  body: unknown,
  onEvent: (event: JsonStreamEvent<T>) => void | Promise<void>,
): Promise<void> {
  const headers = new Headers();
  headers.set("Accept", "text/event-stream");
  headers.set("Content-Type", "application/json");
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const response = await fetch(`${apiBase}${path}`, { method: "POST", body: JSON.stringify(body), headers });
  if (response.status === 401) {
    setAuthToken("");
  }
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    throw new ApiError(response.status, typeof payload === "object" && payload ? payload.detail : payload);
  }
  if (!response.body) {
    throw new ApiError(response.status, "当前浏览器不支持流式响应读取");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const event = parseSseBlock(block);
      if (event) await onEvent(event as JsonStreamEvent<T>);
    }
    if (done) break;
  }

  const event = parseSseBlock(buffer);
  if (event) await onEvent(event as JsonStreamEvent<T>);
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function patchJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export function putJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export function formatBytes(value?: number | null): string {
  if (!value) return "-";
  if (value > 1024 * 1024) return `${(value / 1024 / 1024).toFixed(1)} MB`;
  if (value > 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${value} B`;
}
