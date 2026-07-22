import { Modal } from "antd";

import type { CatalogNodeCard } from "../../api/catalogTree";

export function catalogArchiveMutationVariables(node: CatalogNodeCard) {
  return {
    nodeId: node.node_id,
    action: "archive" as const,
    includeSubtree: true,
    archiveFinalPlacement: true,
  };
}

function archiveConfirmationCopy(node: CatalogNodeCard): { title: string; content: string } {
  if (node.node_kind === "directory") {
    return {
      title: "归档目录及全部下级内容？",
      content:
        "目录、子目录和点位都会从常规目录隐藏；如果其中包含某个实验的最后一个目录位置，也会一并归档。学习内容、视频和历史记录仍会保留，可从归档视图恢复。",
    };
  }

  const activePlacementCount = Number(node.active_placement_count ?? 0);
  if (activePlacementCount <= 1) {
    return {
      title: "归档该实验的最后一个目录位置？",
      content:
        "归档后，学生端将不再通过目录看到该实验。学习内容、视频和历史记录仍会保留，可从归档视图恢复。",
    };
  }

  return {
    title: "归档这个实验位置？",
    content: "只归档当前目录位置；同一实验在其他目录中的位置不受影响。",
  };
}

export function confirmCatalogNodeArchive(
  node: CatalogNodeCard,
  onConfirm: (variables: ReturnType<typeof catalogArchiveMutationVariables>) => Promise<unknown> | unknown,
) {
  const copy = archiveConfirmationCopy(node);
  Modal.confirm({
    title: copy.title,
    content: copy.content,
    okText: "确认归档",
    okButtonProps: { danger: true },
    cancelText: "再想想",
    onOk: () => onConfirm(catalogArchiveMutationVariables(node)),
  });
}
