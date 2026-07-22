import { useQuery } from "@tanstack/react-query";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type { AIConfiguration } from "../../api/settings";
import { api } from "../../api/http";
import type { TeacherCatalogIndexDiagnostics, TeacherCatalogSearchDiagnostics } from "./monitoringTypes";

export function useMonitoringData(retrievalQuery: string) {
  const aiConfig = useQuery({
    queryKey: ["ai-configuration"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });
  const assistantRuntime = useQuery({
    queryKey: ["learning-assistant-runtime", "ai-config"],
    queryFn: () => api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime"),
    enabled: Boolean(aiConfig.data),
    refetchInterval: 10000,
    refetchIntervalInBackground: true,
  });
  const indexDiagnostics = useQuery({
    queryKey: ["teacher-catalog-index-diagnostics"],
    queryFn: () => api<TeacherCatalogIndexDiagnostics>("/api/admin/catalog/search/index/diagnostics"),
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
  });
  const searchDiagnostics = useQuery({
    queryKey: ["teacher-catalog-search-diagnostics", retrievalQuery],
    queryFn: () =>
      api<TeacherCatalogSearchDiagnostics>(
        `/api/admin/catalog/search/query/diagnostics?q=${encodeURIComponent(retrievalQuery)}&limit=8`,
      ),
    enabled: retrievalQuery.trim().length > 0,
  });
  return { aiConfig, assistantRuntime, indexDiagnostics, searchDiagnostics };
}
