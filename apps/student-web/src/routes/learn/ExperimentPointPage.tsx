import { useNavigate, useParams, useSearch } from "@tanstack/react-router";

import { navigateToAiChat, navigateToAssessmentSession, navigateToPoint } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { useDetailBack } from "../../app/shell/useDetailBack";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import type { StudentPointDetailResponse } from "../../api";
import { CatalogPointDetailPanel } from "../../features/catalog/CatalogPointDetailPanel";

export function ExperimentPointPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { nodeId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const goBack = useDetailBack(search.from || "chapter");
  const { canUseAssistant, startAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();
  const nodeId = params.nodeId || "";

  const finishLearning = async (_detail: StudentPointDetailResponse | null) => {
    const posttest = await startAssessmentSession();
    if (posttest) navigateToAssessmentSession(navigate, posttest.session_id, "point");
  };

  return (
    <CatalogPointDetailPanel
      nodeId={nodeId}
      search={search}
      onBack={goBack}
      onFinishLearning={finishLearning}
      finishing={posttestLoading}
      finishError={posttestError}
      assistantEnabled={canUseAssistant}
      onOpenAssistant={(context) => navigateToAiChat(navigate, context, "point")}
      onOpenRelatedPoint={(targetNodeId, pointTitle) =>
        navigateToPoint(navigate, targetNodeId, {
          from: "point",
          profileId: search.profileId,
          chapterId: search.chapterId,
          sourceNodeId: nodeId,
          pointTitle,
        })
      }
    />
  );
}
