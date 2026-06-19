import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { ExperimentDetailPanel } from "../../features/experiments/ExperimentDetailPanel";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { navigateToAiChat, navigateToAssessmentSession } from "../../app/router/navigation";
import { useDetailBack } from "../../app/shell/useDetailBack";
import { useStudentRuntime } from "../../app/shell/studentAppContext";

export function ExperimentPointPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { experimentId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const goBack = useDetailBack(search.from || "chapter");
  const { canUseAssistant, startAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();
  const experimentId = params.experimentId || "";

  const finishLearning = async () => {
    const posttest = await startAssessmentSession();
    if (posttest) navigateToAssessmentSession(navigate, posttest.session_id, "point");
  };

  return (
    <ExperimentDetailPanel
      experimentId={experimentId}
      profileId={search.profileId}
      propertyKey={search.propertyKey}
      propertyTitle={search.propertyTitle}
      elementSymbol={search.elementSymbol}
      chapterView={search.chapterView}
      pointKey={search.pointKey}
      pointTitle={search.pointTitle}
      onBack={goBack}
      onFinishLearning={finishLearning}
      finishing={posttestLoading}
      finishError={posttestError}
      assistantEnabled={canUseAssistant}
      onOpenAssistant={(context) => navigateToAiChat(navigate, context, "point")}
    />
  );
}
