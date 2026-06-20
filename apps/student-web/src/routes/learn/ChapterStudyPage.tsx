import { useCallback, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { navigateToCatalogNode, navigateToElement, navigateToPoint } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { CatalogChapterPanel } from "../../features/catalog/CatalogChapterPanel";
import { catalogPathLabel } from "../../features/catalog/CatalogNodeCards";
import { LearningHomePanel } from "../../features/learning/LearningHomePanel";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
import type { StudentCatalogNodeCard } from "../../api";
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
  const [activeProfile, setActiveProfile] = useState<StudentLearningProfile | null>(null);
  const profileId = params.profileId || "";

  const rememberLearningProfile = useCallback((profile: StudentLearningProfile) => {
    setHeaderMeta(learningHeaderMetaForProfile(profile));
    setActiveProfile(profile);
  }, []);

  const openDirectory = useCallback(
    (node: StudentCatalogNodeCard) => {
      navigateToCatalogNode(navigate, node.node_id, {
        from: "chapter",
        profileId,
        chapterId: node.chapter_id,
        catalogPath: catalogPathLabel([{ node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }]),
      });
    },
    [navigate, profileId],
  );

  const openPoint = useCallback(
    (node: StudentCatalogNodeCard) => {
      navigateToPoint(navigate, node.shortcut_target_node_id || node.node_id, {
        from: "chapter",
        profileId,
        chapterId: node.chapter_id,
        sourceNodeId: node.node_kind === "shortcut" ? node.node_id : "",
        catalogPath: catalogPathLabel([{ node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }]),
        pointTitle: node.title,
      });
    },
    [navigate, profileId],
  );

  return (
    <DetailPageFrame title={headerMeta?.title || "章节学习"} source={search.from}>
      <LearningHomePanel
        profileId={profileId}
        initialElementSymbol={search.elementSymbol}
        onProfileLoaded={rememberLearningProfile}
        onOpenElementDetail={(nextProfileId, symbol) => navigateToElement(navigate, nextProfileId, symbol, { from: "chapter" })}
      />
      <CatalogChapterPanel
        chapterId={activeProfile?.chapter_id}
        profileId={activeProfile?.profile_id || profileId}
        onOpenDirectory={openDirectory}
        onOpenPoint={openPoint}
      />
    </DetailPageFrame>
  );
}
