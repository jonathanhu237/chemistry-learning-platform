import { useCallback, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { Atom, MessageCircle } from "lucide-react";
import { navigateToAiChat, navigateToAssessmentSession, navigateToPoint, navigateToRoot } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { LearningHomePanel } from "../../features/learning/LearningHomePanel";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
import { type AssistantContext } from "../../features/assistant/assistantContext";
import type { StudentLearningProfile, StudentLearningProfileSummary } from "../../api";
import { compactText } from "../../shared/utils/text";

type LearningHeaderMeta = {
  profileId: string;
  chapterId?: string | null;
  title: string;
  subtitle: string;
  summary: string;
};

function learningHeaderMetaForProfile(profile: StudentLearningProfile | StudentLearningProfileSummary): LearningHeaderMeta {
  const title = formatChapterEntryTitle(profile);
  const subtitle = compactText(["当前章节", profile.subtitle].filter(Boolean));
  const summary = compactText([
    profile.subtitle,
    profile.family_name,
    profile.element_symbols.length ? `元素：${profile.element_symbols.join("、")}` : "",
  ]);
  return {
    profileId: profile.profile_id,
    chapterId: profile.chapter_id,
    title,
    subtitle,
    summary: summary || title,
  };
}

export function ChapterStudyPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { profileId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const { canUseAssistant, startAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();
  const [headerMeta, setHeaderMeta] = useState<LearningHeaderMeta | null>(null);
  const profileId = params.profileId || "";

  const rememberLearningProfile = useCallback((profile: StudentLearningProfile) => {
    setHeaderMeta(learningHeaderMetaForProfile(profile));
  }, []);

  const openChapterAssistant = () => {
    if (!headerMeta) return;
    const context: AssistantContext = {
      context_type: "learning_profile",
      context_title: headerMeta.title,
      context_summary: headerMeta.summary,
      chapter_id: headerMeta.chapterId,
      prompts: ["帮我梳理本章重点", "我应该先复习哪一块？", "解释一个本章实验现象"],
    };
    navigateToAiChat(navigate, context, "chapter");
  };

  const finishLearning = async () => {
    const posttest = await startAssessmentSession();
    if (posttest) navigateToAssessmentSession(navigate, posttest.session_id, "chapter");
  };

  const actions = (
    <>
      {canUseAssistant ? (
        <button className="student-app-header-action" type="button" onClick={openChapterAssistant} disabled={!headerMeta}>
          <MessageCircle size={18} />
          <span>问 AI</span>
        </button>
      ) : null}
      <button className="student-app-header-action" type="button" onClick={() => navigateToRoot(navigate, "learn")}>
        <Atom size={18} />
        <span>选章节</span>
      </button>
    </>
  );

  return (
    <DetailPageFrame title={headerMeta?.title || "章节学习"} source={search.from} actions={actions}>
      <LearningHomePanel
        profileId={profileId}
        initialPropertyKey={search.propertyKey}
        initialElementSymbol={search.elementSymbol}
        initialChapterView={search.chapterView}
        onProfileLoaded={rememberLearningProfile}
        onSelectPoint={(point) =>
          navigateToPoint(navigate, point.experimentId, {
            from: "chapter",
            profileId: point.profileId,
            propertyKey: point.propertyKey,
            propertyTitle: point.propertyTitle,
            elementSymbol: point.elementSymbol,
            chapterView: point.chapterView,
            pointKey: point.pointKey,
            pointTitle: point.pointTitle,
          })
        }
        onFinishLearning={finishLearning}
        finishing={posttestLoading}
        finishError={posttestError}
      />
    </DetailPageFrame>
  );
}
