import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { FlaskConical, FolderOpen, LoaderCircle } from "lucide-react";

import {
  errorMessage,
  getPreviewCatalogNode,
  getPreviewCatalogPointDetail,
  previewMediaUrl,
  type CatalogPreviewNodeResponse,
  type StudentCatalogChapterResponse,
  type StudentCatalogNodeCard,
  type StudentCatalogNodeResponse,
  type StudentLearningPageResponse,
  type StudentPointDetailResponse,
} from "../../api";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { CatalogPointDetailPanel } from "../../features/catalog/CatalogPointDetailPanel";
import { LearningState } from "../../shared/mobile/LearningState";
import { FamilyCatalogShell } from "./FamilyCatalogShell";
import { previewBackOrClose } from "./previewNavigation";

type PreviewNodeSearch = StudentRouteSearch & {
  preview_token?: string;
};

export function PreviewCatalogNodePage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { nodeId?: string };
  const search = useSearch({ strict: false }) as PreviewNodeSearch;
  const nodeId = params.nodeId || "";
  const previewToken = search.preview_token || "";
  const [payload, setPayload] = useState<CatalogPreviewNodeResponse | null>(null);
  const [familyTitle, setFamilyTitle] = useState("章节学习");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setPayload(null);
    setLoading(true);
    setError("");
    getPreviewCatalogNode(nodeId, previewToken)
      .then((nextPayload) => {
        if (!cancelled) setPayload(nextPayload);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [nodeId, previewToken]);

  const openPreviewNode = useCallback(
    (node: StudentCatalogNodeCard) => {
      void navigate({
        to: "/preview/catalog/nodes/$nodeId",
        params: { nodeId: node.node_id },
        search: { preview_token: previewToken },
      });
    },
    [navigate, previewToken],
  );

  const loadPreviewLearningPage = useCallback(async (): Promise<StudentLearningPageResponse> => {
    if (payload?.node_kind === "directory" && payload.learning_page) return payload.learning_page;
    throw new Error("Preview learning page is not available for this catalog directory");
  }, [payload]);

  const loadPreviewChapterCatalog = useCallback(
    async (chapterId: string): Promise<StudentCatalogChapterResponse> => ({
      chapter_id: chapterId,
      chapter_title: payload?.learning_page?.active_profile?.title || payload?.directory?.node.title || "章节学习",
      nodes: payload?.directory ? [payload.directory.node] : [],
    }),
    [payload],
  );

  const loadDirectory = useCallback(
    async (targetNodeId: string): Promise<StudentCatalogNodeResponse> => {
      if (payload?.node_kind === "directory" && payload.directory?.node.node_id === targetNodeId) {
        return payload.directory;
      }
      const nextPayload = await getPreviewCatalogNode(targetNodeId, previewToken);
      if (nextPayload.node_kind !== "directory" || !nextPayload.directory) {
        throw new Error("Catalog node is not a directory");
      }
      return nextPayload.directory;
    },
    [payload, previewToken],
  );

  const loadPointDetail = useCallback(
    (targetNodeId: string): Promise<StudentPointDetailResponse> => {
      if (payload?.node_kind === "point" && payload.point?.node_id === targetNodeId) {
        return Promise.resolve(payload.point);
      }
      return getPreviewCatalogPointDetail(targetNodeId, previewToken);
    },
    [payload, previewToken],
  );

  const ignoreFinish = async (_detail: StudentPointDetailResponse | null) => undefined;

  if (loading) {
    return (
      <main className="student-preview-page">
        <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载预览" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="student-preview-page">
        <LearningState icon={<FolderOpen size={23} />} text={error} />
      </main>
    );
  }

  if (payload?.node_kind === "directory" && payload.directory) {
    const activeProfile = payload.learning_page?.active_profile;
    if (!activeProfile) {
      return (
        <main className="student-preview-page">
          <LearningState icon={<FolderOpen size={23} />} text="当前目录未匹配到学生二级目录页" />
        </main>
      );
    }
    return (
      <main className="student-preview-page">
        <DetailPageFrame title={familyTitle} source={search.from} className="family-detail-frame" onBack={previewBackOrClose}>
          <FamilyCatalogShell
            profileId={activeProfile.profile_id}
            directoryNodeId={nodeId}
            initialElementSymbol={search.elementSymbol || activeProfile.default_element_symbol || activeProfile.element_symbols[0] || ""}
            initialPage={payload.learning_page}
            loadLearningPage={loadPreviewLearningPage}
            loadChapterCatalog={loadPreviewChapterCatalog}
            loadCatalogNode={loadDirectory}
            onOpenDirectoryOverride={openPreviewNode}
            onOpenPointOverride={openPreviewNode}
            onOpenSearchOverride={() => undefined}
            onOpenElementDetailOverride={() => undefined}
            onTitleChange={setFamilyTitle}
          />
        </DetailPageFrame>
      </main>
    );
  }

  if (payload?.node_kind === "point" && payload.point) {
    return (
      <main className="student-preview-page">
        <CatalogPointDetailPanel
          nodeId={nodeId}
          search={search}
          onBack={previewBackOrClose}
          onFinishLearning={ignoreFinish}
          finishing={false}
          finishError=""
          assistantEnabled={false}
          onOpenAssistant={() => undefined}
          onOpenRelatedPoint={() => undefined}
          previewMode
          loadPointDetail={loadPointDetail}
          resolveMediaUrl={previewMediaUrl}
        />
      </main>
    );
  }

  return (
    <main className="student-preview-page">
      <LearningState icon={<FlaskConical size={23} />} text="预览节点不可用" />
    </main>
  );
}
