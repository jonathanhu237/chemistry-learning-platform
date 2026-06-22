import { useEffect, useState } from "react";
import { FolderOpen, LoaderCircle } from "lucide-react";

import type { StudentCatalogNodeCard, StudentCatalogNodeResponse } from "../../api";
import { errorMessage, getStudentCatalogNode } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { CatalogNodeCards, catalogPathLabel } from "./CatalogNodeCards";

export function CatalogDirectoryPanel({
  nodeId,
  onLoaded,
  onOpenDirectory,
  onOpenPoint,
  searchQuery = "",
  variant = "panel",
}: {
  nodeId: string;
  onLoaded?: (node: StudentCatalogNodeResponse) => void;
  onOpenDirectory: (node: StudentCatalogNodeCard) => void;
  onOpenPoint: (node: StudentCatalogNodeCard) => void;
  searchQuery?: string;
  variant?: "panel" | "body";
}) {
  const [detail, setDetail] = useState<StudentCatalogNodeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentCatalogNode(nodeId)
      .then((payload) => {
        if (cancelled) return;
        setDetail(payload);
        onLoaded?.(payload);
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
  }, [nodeId, onLoaded]);

  if (loading) return <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载目录" />;
  if (error) return <LearningState icon={<FolderOpen size={23} />} text={error} />;
  if (!detail) return null;

  const pathText = catalogPathLabel(detail.breadcrumbs);

  return (
    <section className={variant === "body" ? "catalog-directory-panel catalog-browser-body" : "learning-panel catalog-directory-panel"} aria-label="目录详情">
      <div className={variant === "body" ? "catalog-browser-head" : "catalog-panel-head"}>
        <p>{pathText}</p>
        <h2>{detail.node.title}</h2>
        {detail.node.summary ? <span>{detail.node.summary}</span> : null}
      </div>
      {detail.children.length ? (
        <CatalogNodeCards
          nodes={detail.children}
          breadcrumbs={detail.breadcrumbs}
          searchQuery={searchQuery}
          onOpenDirectory={onOpenDirectory}
          onOpenPoint={onOpenPoint}
        />
      ) : (
        <MobileEmptyState className="empty-learning-card" icon={<FolderOpen size={20} />}>
          <span>当前目录暂无子节点</span>
        </MobileEmptyState>
      )}
    </section>
  );
}
