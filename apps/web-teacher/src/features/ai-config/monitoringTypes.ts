import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type { AIConfiguration } from "../../api/settings";

export type UsageRange = "1d" | "7d" | "30d";

export type MonitorModuleKey =
  | "overview"
  | "openai"
  | "rag"
  | "es"
  | "dictionary"
  | "guardrail"
  | "trends";

export type MonitorTone = "good" | "warn" | "bad" | "idle" | "legacy" | "muted";

export type TeacherCatalogIndexDiagnostics = {
  settings?: {
    backend?: string;
    index?: string;
    desired_mapping_version?: string;
    analyzer?: string;
    local_fallback?: boolean;
    analyzer_assets?: {
      ok?: boolean;
      missing?: string[];
      total_dictionary_lines?: number;
      files?: Array<{
        id?: string;
        path?: string;
        exists?: boolean;
        line_count?: number | null;
        sha256?: string;
      }>;
    };
    dictionary_assets?: {
      version?: string;
      category_counts?: Record<string, number>;
    };
  };
  postgres?: {
    published_point_content_count?: number;
    sync_status_counts?: Record<string, number>;
  };
  elasticsearch?: {
    configured?: boolean;
    document_count?: number;
    health?: { status?: string };
    mapping?: {
      version?: string;
      desired_version?: string;
      chemistry_fields_present?: Record<string, boolean>;
    };
    error?: string;
  };
};

export type TeacherCatalogSearchDiagnostics = {
  status?: string;
  backend?: string;
  query_plan?: {
    terms?: {
      formulae?: string[];
      strict_aliases?: string[];
      reagent_aliases?: string[];
      condition_tags?: string[];
      phenomenon_tags?: string[];
      property_tags?: string[];
      reaction_features?: string[];
    };
    routes?: Array<{ name: string; label: string; fields?: string[]; weight?: number; enabled?: boolean }>;
  };
  results?: Array<{
    id: string;
    title: string;
    subtitle?: string;
    score?: number;
    matched_routes?: string[];
    formulae?: string[];
    condition_tags?: string[];
    phenomenon_tags?: string[];
    property_tags?: string[];
  }>;
  error?: string;
};

export type MonitoringQueries = {
  aiConfig: {
    data?: AIConfiguration;
    error: unknown;
    isLoading: boolean;
    isFetching: boolean;
    dataUpdatedAt: number;
    refetch: () => Promise<unknown>;
  };
  assistantRuntime: {
    data?: LearningAssistantRuntime;
    error: unknown;
    isLoading: boolean;
    isFetching: boolean;
    isError: boolean;
    dataUpdatedAt: number;
    refetch: () => Promise<unknown>;
  };
  indexDiagnostics: {
    data?: TeacherCatalogIndexDiagnostics;
    error: unknown;
    isLoading: boolean;
    isFetching: boolean;
    dataUpdatedAt: number;
    refetch: () => Promise<unknown>;
  };
  searchDiagnostics: {
    data?: TeacherCatalogSearchDiagnostics;
    error: unknown;
    isLoading: boolean;
    isFetching: boolean;
    dataUpdatedAt: number;
    refetch: () => Promise<unknown>;
  };
};

export type HealthTile = {
  key: MonitorModuleKey;
  label: string;
  status: string;
  value: string;
  tone: MonitorTone;
  detail?: string;
};

export type AttentionItem = {
  key: string;
  module: MonitorModuleKey;
  title: string;
  detail: string;
  tone: Exclude<MonitorTone, "good" | "muted">;
};
