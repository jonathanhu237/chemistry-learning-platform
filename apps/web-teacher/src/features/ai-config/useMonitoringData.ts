import { useQuery } from "@tanstack/react-query";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type { AIConfiguration } from "../../api/settings";
import { api } from "../../api/http";
import type { VideoLibraryIndexDiagnostics, VideoLibrarySearchDiagnostics } from "./monitoringTypes";

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
    queryKey: ["video-library-index-diagnostics"],
    queryFn: () => api<VideoLibraryIndexDiagnostics>("/api/admin/video-library/index/diagnostics"),
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
  });
  const searchDiagnostics = useQuery({
    queryKey: ["video-library-search-diagnostics", retrievalQuery],
    queryFn: () =>
      api<VideoLibrarySearchDiagnostics>(
        `/api/admin/video-library/search/diagnostics?q=${encodeURIComponent(retrievalQuery)}&limit=8`,
      ),
    enabled: retrievalQuery.trim().length > 0,
  });
  return { aiConfig, assistantRuntime, indexDiagnostics, searchDiagnostics };
}
