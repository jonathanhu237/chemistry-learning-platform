import { useEffect, useState } from "react";
import { BookOpen, LoaderCircle } from "lucide-react";

import type { StudentCatalogChapterResponse, StudentCatalogNodeCard } from "../../api";
import { errorMessage, getStudentChapterCatalog } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { CatalogNodeCards } from "./CatalogNodeCards";

export function CatalogChapterPanel({
  chapterId,
  profileId,
  onOpenDirectory,
  onOpenPoint,
  searchQuery = "",
  variant = "panel",
}: {
  chapterId?: string | null;
  profileId?: string | null;
  onOpenDirectory: (node: StudentCatalogNodeCard) => void;
  onOpenPoint: (node: StudentCatalogNodeCard) => void;
  searchQuery?: string;
  variant?: "panel" | "body";
}) {
  const [catalog, setCatalog] = useState<StudentCatalogChapterResponse | null>(null);
  const [loading, setLoading] = useState(Boolean(chapterId));
  const [error, setError] = useState("");

  useEffect(() => {
    if (!chapterId) {
      setCatalog(null);
      setLoading(false);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentChapterCatalog(chapterId)
      .then((payload) => {
        if (!cancelled) setCatalog(payload);
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
  }, [chapterId]);

  if (loading) return <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载章节目录" />;
  if (error) return <LearningState icon={<BookOpen size={23} />} text={error} />;
  if (!catalog?.nodes.length) {
    return (
      <MobileEmptyState className="empty-learning-card" icon={<BookOpen size={20} />}>
        <span>本章节暂无已发布目录</span>
      </MobileEmptyState>
    );
  }

  return (
    <section className={variant === "body" ? "catalog-chapter-panel catalog-browser-body" : "catalog-chapter-panel"} aria-label="章节目录">
      <div className={variant === "body" ? "catalog-browser-head catalog-browser-head-compact" : "catalog-panel-head"}>
        <p>{profileId ? "章节学习目录" : "目录"}</p>
        {variant === "body" ? null : <h2>{catalog.chapter_title}</h2>}
        <span>{catalog.nodes.length} 个入口</span>
      </div>
      <CatalogNodeCards nodes={catalog.nodes} breadcrumbs={[]} searchQuery={searchQuery} onOpenDirectory={onOpenDirectory} onOpenPoint={onOpenPoint} />
    </section>
  );
}
