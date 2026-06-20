import { BookOpen, ChevronRight, FileVideo, FolderOpen, Link, PlayCircle } from "lucide-react";

import type { StudentCatalogBreadcrumb, StudentCatalogNodeCard } from "../../api";

export function catalogPathLabel(path: StudentCatalogBreadcrumb[]): string {
  return path.map((item) => item.title).filter(Boolean).join(" / ");
}

export function isPointNode(node: StudentCatalogNodeCard): boolean {
  return node.node_kind === "point" || node.node_kind === "hybrid";
}

function nodeIcon(node: StudentCatalogNodeCard) {
  if (node.node_kind === "shortcut") return <Link size={20} />;
  if (node.node_kind === "point") return <PlayCircle size={20} />;
  if (node.node_kind === "hybrid") return <FileVideo size={20} />;
  return <FolderOpen size={20} />;
}

function nodeMeta(node: StudentCatalogNodeCard): string {
  if (node.node_kind === "shortcut") return "快捷入口";
  if (node.node_kind === "hybrid") return `目录 + 点位 · ${node.published_media_count || node.media_count} 个视频`;
  if (node.node_kind === "point") return `${node.published_media_count || node.media_count} 个视频`;
  return node.has_children ? "继续学习" : "待发布内容";
}

export function CatalogNodeCards({
  nodes,
  breadcrumbs,
  onOpenDirectory,
  onOpenPoint,
}: {
  nodes: StudentCatalogNodeCard[];
  breadcrumbs: StudentCatalogBreadcrumb[];
  onOpenDirectory: (node: StudentCatalogNodeCard) => void;
  onOpenPoint: (node: StudentCatalogNodeCard) => void;
}) {
  return (
    <div className="catalog-node-grid">
      {nodes.map((node) => {
        const pointCapable = isPointNode(node);
        const opensDirectory = node.node_kind === "directory" || node.node_kind === "hybrid";
        return (
          <div
            className={`catalog-node-card kind-${node.node_kind}`}
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
                {node.summary ? <small>{node.summary}</small> : null}
                <em>{nodeMeta(node)}</em>
              </span>
              <ChevronRight size={18} />
            </button>
            {pointCapable && opensDirectory ? (
              <button className="catalog-node-point-action" type="button" onClick={() => onOpenPoint(node)}>
                点位视频
              </button>
            ) : null}
            <span className="catalog-node-card-path">{catalogPathLabel([...breadcrumbs, { node_id: node.node_id, title: node.title, node_kind: node.node_kind, chapter_id: node.chapter_id }])}</span>
          </div>
        );
      })}
    </div>
  );
}
