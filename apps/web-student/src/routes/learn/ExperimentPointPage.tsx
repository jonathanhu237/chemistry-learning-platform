import { useNavigate, useParams, useSearch } from "@tanstack/react-router";

import { navigateToAiChat, navigateToAssessmentSession, navigateToPoint } from "../../app/router/navigation";
import { storePosttestSessionNotice } from "../../app/router/assessmentSessionStore";
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
  const { canUseAssistant, startPointAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();
  const nodeId = params.nodeId || "";

  const finishLearning = async (detail: StudentPointDetailResponse | null) => {
    const pointNodeId = detail?.assessment_context.point_node_id || nodeId;
    const posttest = await startPointAssessmentSession(pointNodeId);
    if (!posttest) return;
    if (posttest.assessment_mode !== "point") {
      storePosttestSessionNotice(posttest.session_id, "你还有一轮未完成测评，已为你继续打开原测评。完成后再回到本点位测一测。");
    }
    navigateToAssessmentSession(navigate, posttest.session_id, "point");
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
