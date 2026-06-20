import { useCallback, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";

import { navigateToCatalogNode, navigateToPoint } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import type { StudentCatalogNodeCard, StudentCatalogNodeResponse } from "../../api";
import { CatalogDirectoryPanel } from "../../features/catalog/CatalogDirectoryPanel";
import { catalogPathLabel } from "../../features/catalog/CatalogNodeCards";

export function CatalogDirectoryPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { nodeId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const [detail, setDetail] = useState<StudentCatalogNodeResponse | null>(null);
  const nodeId = params.nodeId || "";
  const title = detail?.node.title || "目录";

  const openDirectory = useCallback(
    (node: StudentCatalogNodeCard) => {
      navigateToCatalogNode(navigate, node.node_id, {
        from: "chapter",
        profileId: search.profileId,
        chapterId: node.chapter_id,
        catalogPath: detail ? catalogPathLabel([...detail.breadcrumbs, { node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }]) : "",
      });
    },
    [detail, navigate, search.profileId],
  );

  const openPoint = useCallback(
    (node: StudentCatalogNodeCard) => {
      navigateToPoint(navigate, node.shortcut_target_node_id || node.node_id, {
        from: "chapter",
        profileId: search.profileId,
        chapterId: node.chapter_id,
        sourceNodeId: node.node_kind === "shortcut" ? node.node_id : "",
        catalogPath: detail ? catalogPathLabel([...detail.breadcrumbs, { node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }]) : "",
        pointTitle: node.title,
      });
    },
    [detail, navigate, search.profileId],
  );

  return (
    <DetailPageFrame title={title} source={search.from}>
      <CatalogDirectoryPanel nodeId={nodeId} onLoaded={setDetail} onOpenDirectory={openDirectory} onOpenPoint={openPoint} />
    </DetailPageFrame>
  );
}
