import { useCallback, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { MessageCircle } from "lucide-react";
import { navigateToAiChat, navigateToElement, navigateToPoint } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { type AssistantContext } from "../../features/assistant/assistantContext";
import { LearningHomePanel } from "../../features/learning/LearningHomePanel";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
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
  const { canUseAssistant } = useStudentRuntime();
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
      prompts: ["帮我理解本章重点", "我应该先学哪个实验？", "解释一个本章常见考点"],
    };
    navigateToAiChat(navigate, context, "chapter");
  };

  const actions = canUseAssistant ? (
    <button className="student-app-header-action" type="button" onClick={openChapterAssistant} disabled={!headerMeta}>
      <MessageCircle size={18} />
      <span>问 AI</span>
    </button>
  ) : null;

  return (
    <DetailPageFrame title={headerMeta?.title || "章节学习"} source={search.from} actions={actions}>
      <LearningHomePanel
        profileId={profileId}
        initialElementSymbol={search.elementSymbol}
        onProfileLoaded={rememberLearningProfile}
        onOpenElementDetail={(nextProfileId, symbol) => navigateToElement(navigate, nextProfileId, symbol, { from: "chapter" })}
        onSelectPoint={(point) =>
          navigateToPoint(navigate, point.experimentId, {
            from: "chapter",
            profileId: point.profileId,
            propertyKey: point.propertyKey,
            propertyTitle: point.propertyTitle,
            elementSymbol: point.elementSymbol,
            pointKey: point.pointKey,
            pointTitle: point.pointTitle,
          })
        }
      />
    </DetailPageFrame>
  );
}
