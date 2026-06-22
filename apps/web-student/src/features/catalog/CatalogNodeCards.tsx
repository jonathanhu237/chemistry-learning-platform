import { ChevronRight, FolderOpen, PlayCircle } from "lucide-react";

import type { StudentCatalogBreadcrumb, StudentCatalogNodeCard } from "../../api";

export function catalogPathLabel(path: StudentCatalogBreadcrumb[]): string {
  return path.map((item) => item.title).filter(Boolean).join(" / ");
}

export function isPointNode(node: StudentCatalogNodeCard): boolean {
  return node.node_kind === "point";
}

function nodeIcon(node: StudentCatalogNodeCard) {
  if (node.node_kind === "point") return <PlayCircle size={20} />;
  return <FolderOpen size={20} />;
}

function nodeMeta(node: StudentCatalogNodeCard): string {
  if (node.node_kind === "point") return (node.published_media_count || node.media_count) > 0 ? "有视频" : "暂无视频";
  return node.has_children ? "继续学习" : "待发布内容";
}

function nodeDescription(node: StudentCatalogNodeCard): string {
  return node.summary || "";
}

export function CatalogNodeCards({
  nodes,
  breadcrumbs,
  searchQuery = "",
  onOpenDirectory,
  onOpenPoint,
}: {
  nodes: StudentCatalogNodeCard[];
  breadcrumbs: StudentCatalogBreadcrumb[];
  searchQuery?: string;
  onOpenDirectory: (node: StudentCatalogNodeCard) => void;
  onOpenPoint: (node: StudentCatalogNodeCard) => void;
}) {
  const query = searchQuery.trim().toLowerCase();
  const visibleNodes = query
    ? nodes.filter((node) => {
        const path = catalogPathLabel([...breadcrumbs, { node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }]);
        return [node.title, node.summary, nodeMeta(node), path].filter(Boolean).join(" ").toLowerCase().includes(query);
      })
    : nodes;

  if (!visibleNodes.length) {
    return (
      <div className="catalog-node-empty">
        <span>未找到匹配目录</span>
      </div>
    );
  }

  return (
    <div className="catalog-node-grid">
      {visibleNodes.map((node) => {
        const pointCapable = isPointNode(node);
        const opensDirectory = node.node_kind === "directory";
        const description = nodeDescription(node);
        return (
          <div
            className={`catalog-node-card kind-${node.node_kind} layout-default`}
            key={node.node_id}
          >
            <button
              className="catalog-node-card-main"
              type="button"
              onClick={() => {
                if (pointCapable && !opensDirectory) onOpenPoint(node);
                else onOpenDirectory(node);
              }}
            >
              <span className="catalog-node-card-icon">{nodeIcon(node)}</span>
              <span className="catalog-node-card-copy">
                <strong>{node.title}</strong>
                {description ? <small>{description}</small> : null}
                <em>{nodeMeta(node)}</em>
              </span>
              <ChevronRight size={18} />
            </button>
            <span className="catalog-node-card-path">{catalogPathLabel([...breadcrumbs, { node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }])}</span>
          </div>
        );
      })}
    </div>
  );
}
