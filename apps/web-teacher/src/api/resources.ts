import { api } from "./http";

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

export function listChapters(): Promise<Chapter[]> {
  return api<Chapter[]>("/api/chapters");
}

export function getLearningResourceOverview(): Promise<LearningResourceOverview> {
  return api<LearningResourceOverview>("/api/admin/learning-resources/overview");
}
