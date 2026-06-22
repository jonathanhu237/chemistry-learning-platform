import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  bindCatalogPointMedia,
  changeCatalogMediaBindingStatus,
  changeCatalogNodeStatus,
  changeCatalogPointContentPublication,
  copyCatalogNode,
  createCatalogPointPreviewToken,
  createCatalogNode,
  getCatalogChapterTreeSummary,
  getCatalogNode,
  getCatalogPointAiContext,
  listCatalogCandidateMedia,
  listCatalogChildren,
  listCatalogRoots,
  moveCatalogNode,
  reorderCatalogNodes,
  runCatalogPointRagProbe,
  saveCatalogPointContent,
  saveCatalogRelatedLinks,
  searchCatalogNodes,
  triggerCatalogPointJob,
  updateCatalogNode,
  validateCatalogNode,
} from "../../api/catalogTree";
import type {
  CatalogNodeCreatePayload,
  CatalogNodeCopyPayload,
  CatalogNodeDetail,
  CatalogNodeMovePayload,
  CatalogPointJobAction,
  CatalogPointRagProbe,
  CatalogNodeUpdatePayload,
  CatalogPointContentPayload,
  CatalogRelatedLinksPayload,
} from "../../api/catalogTree";
import type { MediaAsset } from "../../api/media";
import type { Chapter } from "../../api/resources";
import { listChapters } from "../../api/resources";
import { errorMessage } from "../../lib/errors";

type MessageApi = {
  success: (content: string) => void;
  error: (content: string) => void;
};

export function useCatalogChapters() {
  return useQuery<Chapter[]>({ queryKey: ["chapters"], queryFn: listChapters });
}

export function useCatalogRoots(chapterId?: string, includeArchived = false) {
  return useQuery({
    queryKey: ["catalog-roots", chapterId, includeArchived],
    queryFn: () => listCatalogRoots(chapterId || "", includeArchived),
    enabled: Boolean(chapterId),
  });
}

export function useCatalogChapterTreeSummary(chapterId?: string) {
  return useQuery({
    queryKey: ["catalog-chapter-summary", chapterId],
    queryFn: () => getCatalogChapterTreeSummary(chapterId || ""),
    enabled: Boolean(chapterId),
  });
}

export function useCatalogChildren(nodeId?: string, enabled = true, includeArchived = false) {
  return useQuery({
    queryKey: ["catalog-children", nodeId, includeArchived],
    queryFn: () => listCatalogChildren(nodeId || "", includeArchived),
    enabled: Boolean(nodeId) && enabled,
  });
}

export function useCatalogNodeDetail(nodeId?: string) {
  return useQuery({
    queryKey: ["catalog-node", nodeId],
    queryFn: () => getCatalogNode(nodeId || ""),
    enabled: Boolean(nodeId),
  });
}

export function useCatalogSearch(query: string, chapterId?: string | null, enabled = true, statusFilter = "all") {
  return useQuery({
    queryKey: ["catalog-search", query, chapterId, statusFilter],
    queryFn: () => searchCatalogNodes(query, chapterId, 80, statusFilter),
    enabled: enabled && query.trim().length >= 2,
  });
}

export function useCatalogValidation(nodeId?: string, includeSubtree = false) {
  return useQuery({
    queryKey: ["catalog-validation", nodeId, includeSubtree],
    queryFn: () => validateCatalogNode(nodeId || "", includeSubtree),
    enabled: Boolean(nodeId),
  });
}

export function useCatalogPointAiContext(nodeId?: string, enabled = true) {
  return useQuery({
    queryKey: ["catalog-point-ai-context", nodeId],
    queryFn: () => getCatalogPointAiContext(nodeId || ""),
    enabled: Boolean(nodeId) && enabled,
  });
}

export function useCatalogMediaAssets(enabled: boolean) {
  return useQuery({
    queryKey: ["catalog-media-assets"],
    queryFn: () => listCatalogCandidateMedia(300),
    enabled,
  });
}

export function useCatalogInvalidation() {
  const queryClient = useQueryClient();
  const invalidateCatalog = (detail?: CatalogNodeDetail | null) => {
    void queryClient.invalidateQueries({ queryKey: ["catalog-roots"] });
    void queryClient.invalidateQueries({ queryKey: ["catalog-chapter-summary"] });
    void queryClient.invalidateQueries({ queryKey: ["catalog-children"] });
    void queryClient.invalidateQueries({ queryKey: ["catalog-search"] });
    void queryClient.invalidateQueries({ queryKey: ["catalog-validation"] });
    void queryClient.invalidateQueries({ queryKey: ["catalog-media-assets"] });
    if (detail?.node.node_id) {
      void queryClient.invalidateQueries({ queryKey: ["catalog-node", detail.node.node_id] });
      for (const item of detail.breadcrumbs || []) {
        if (item.node_kind === "directory") {
          void queryClient.invalidateQueries({ queryKey: ["catalog-children", item.node_id] });
        }
      }
      if (detail.node.parent_id) {
        void queryClient.invalidateQueries({ queryKey: ["catalog-children", detail.node.parent_id] });
      }
      void queryClient.invalidateQueries({ queryKey: ["catalog-roots", detail.node.chapter_id] });
    }
  };
  return { invalidateCatalog };
}

export function useCatalogMutations(message: MessageApi) {
  const { invalidateCatalog } = useCatalogInvalidation();
  const queryClient = useQueryClient();

  const createNode = useMutation({
    mutationFn: (payload: CatalogNodeCreatePayload) => createCatalogNode(payload),
    onSuccess: (detail) => {
      message.success("目录节点已创建");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const copyNode = useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: string; payload: CatalogNodeCopyPayload }) => copyCatalogNode(nodeId, payload),
    onSuccess: (detail) => {
      message.success("节点已添加为草稿");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateNode = useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: string; payload: CatalogNodeUpdatePayload; silent?: boolean }) => updateCatalogNode(nodeId, payload),
    onSuccess: (detail, variables) => {
      if (!variables.silent) message.success("节点信息已保存");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const moveNode = useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: string; payload: CatalogNodeMovePayload }) => moveCatalogNode(nodeId, payload),
    onSuccess: (detail) => {
      message.success("节点位置已更新");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const reorderNodes = useMutation({
    mutationFn: reorderCatalogNodes,
    onSuccess: () => {
      message.success("同级顺序已更新");
      invalidateCatalog(null);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const changeNodeStatus = useMutation({
    mutationFn: ({
      nodeId,
      action,
      includeSubtree,
    }: {
      nodeId: string;
      action: "archive" | "restore" | "publish" | "unpublish";
      includeSubtree?: boolean;
    }) => changeCatalogNodeStatus(nodeId, { action, include_subtree: includeSubtree }),
    onSuccess: (detail) => {
      message.success("节点状态已更新");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const createPreviewToken = useMutation({
    mutationFn: ({ nodeId }: { nodeId: string }) => createCatalogPointPreviewToken(nodeId),
    onError: (error) => message.error(errorMessage(error)),
  });

  const savePointContent = useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: string; payload: CatalogPointContentPayload; silent?: boolean }) => saveCatalogPointContent(nodeId, payload),
    onSuccess: (detail, variables) => {
      if (!variables.silent) message.success("点位内容已保存为草稿");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const changePointPublication = useMutation({
    mutationFn: ({ nodeId, action }: { nodeId: string; action: "publish" | "unpublish" | "archive" }) =>
      changeCatalogPointContentPublication(nodeId, action),
    onSuccess: (detail) => {
      message.success("点位发布状态已更新");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveRelatedLinks = useMutation({
    mutationFn: ({ nodeId, payload }: { nodeId: string; payload: CatalogRelatedLinksPayload }) => saveCatalogRelatedLinks(nodeId, payload),
    onSuccess: (detail) => {
      message.success("相关实验已保存");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const bindMedia = useMutation({
    mutationFn: async ({
      nodeId,
      asset,
    }: {
      nodeId: string;
      asset: MediaAsset;
    }) => {
      const result = await bindCatalogPointMedia(nodeId, {
        media_asset_id: asset.id,
        title: asset.title || asset.original_file_name || null,
      });
      return result.detail;
    },
    onSuccess: (detail) => {
      message.success("视频素材已绑定");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const changeMediaStatus = useMutation({
    mutationFn: ({ bindingId, action }: { bindingId: string; action: "publish" | "unpublish" | "delete" }) =>
      changeCatalogMediaBindingStatus(bindingId, action),
    onSuccess: (detail) => {
      message.success("视频绑定状态已更新");
      invalidateCatalog(detail);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const triggerPointJob = useMutation({
    mutationFn: ({ nodeId, action }: { nodeId: string; action: CatalogPointJobAction }) => triggerCatalogPointJob(nodeId, action),
    onSuccess: (state, variables) => {
      message.success("点位同步任务已更新");
      void queryClient.invalidateQueries({ queryKey: ["catalog-node", variables.nodeId] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-validation", variables.nodeId] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-search"] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-point-ai-context", variables.nodeId] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-roots"] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-chapter-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["catalog-children"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const runRagProbe = useMutation<CatalogPointRagProbe, unknown, { nodeId: string }>({
    mutationFn: ({ nodeId }) => runCatalogPointRagProbe(nodeId),
    onError: (error) => message.error(errorMessage(error)),
  });

  return {
    createNode,
    copyNode,
    updateNode,
    moveNode,
    reorderNodes,
    changeNodeStatus,
    createPreviewToken,
    savePointContent,
    changePointPublication,
    saveRelatedLinks,
    bindMedia,
    changeMediaStatus,
    triggerPointJob,
    runRagProbe,
  };
}

export type CatalogMutations = ReturnType<typeof useCatalogMutations>;
