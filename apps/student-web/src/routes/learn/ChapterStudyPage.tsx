import { useCallback, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { navigateToElement, navigateToPoint } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { LearningHomePanel } from "../../features/learning/LearningHomePanel";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
import type { StudentLearningProfile, StudentLearningProfileSummary } from "../../api";

type LearningHeaderMeta = {
  title: string;
};

function learningHeaderMetaForProfile(profile: StudentLearningProfile | StudentLearningProfileSummary): LearningHeaderMeta {
  return {
    title: formatChapterEntryTitle(profile),
  };
}

export function ChapterStudyPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { profileId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const [headerMeta, setHeaderMeta] = useState<LearningHeaderMeta | null>(null);
  const profileId = params.profileId || "";

  const rememberLearningProfile = useCallback((profile: StudentLearningProfile) => {
    setHeaderMeta(learningHeaderMetaForProfile(profile));
  }, []);

  return (
    <DetailPageFrame title={headerMeta?.title || "章节学习"} source={search.from}>
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
