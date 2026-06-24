import { useCallback } from "react";
import { useParams, useSearch } from "@tanstack/react-router";

import { getPreviewCatalogPointDetail, previewMediaUrl, type StudentPointDetailResponse } from "../../api";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { CatalogPointDetailPanel } from "../../features/catalog/CatalogPointDetailPanel";
import { previewBackOrClose } from "./previewNavigation";

type PreviewPointSearch = StudentRouteSearch & {
  preview_token?: string;
};

export function PreviewCatalogPointPage() {
  const params = useParams({ strict: false }) as { nodeId?: string };
  const search = useSearch({ strict: false }) as PreviewPointSearch;
  const nodeId = params.nodeId || "";
  const previewToken = search.preview_token || "";

  const loadPointDetail = useCallback(
    (targetNodeId: string) => getPreviewCatalogPointDetail(targetNodeId, previewToken),
    [previewToken],
  );

  const ignoreFinish = async (_detail: StudentPointDetailResponse | null) => undefined;

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
