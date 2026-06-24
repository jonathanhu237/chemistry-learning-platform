import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Atom, Bookmark, ClipboardList, Eye, FlaskConical, LoaderCircle, MoreHorizontal, PlayCircle, ShieldAlert } from "lucide-react";

import { buildReactionEquationRows } from "../../../../shared/reactionEquations";
import type { StudentPointDetailResponse } from "../../api";
import { errorMessage, getStudentCatalogPointDetail, studentMediaUrl } from "../../api";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { ChemEquation } from "../../components/ChemEquation";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { compactText } from "../../shared/utils/text";
import type { AssistantContext } from "../assistant/assistantContext";
import { catalogPathLabel } from "./CatalogNodeCards";
import { PointVideoPlayer } from "./PointVideoPlayer";

export function CatalogPointDetailPanel({
  nodeId,
  search,
  onBack,
  onFinishLearning,
  finishing,
  finishError,
  assistantEnabled,
  onOpenAssistant,
  onOpenRelatedPoint,
  previewMode = false,
  loadPointDetail = getStudentCatalogPointDetail,
  resolveMediaUrl = studentMediaUrl,
}: {
  nodeId: string;
  search: StudentRouteSearch;
  onBack: () => void;
  onFinishLearning: (detail: StudentPointDetailResponse | null) => void;
  finishing: boolean;
  finishError: string;
  assistantEnabled: boolean;
  onOpenAssistant: (context: AssistantContext) => void;
  onOpenRelatedPoint: (nodeId: string, pointTitle: string) => void;
  previewMode?: boolean;
  loadPointDetail?: (nodeId: string) => Promise<StudentPointDetailResponse>;
  resolveMediaUrl?: (path: string) => string;
}) {
  const [detail, setDetail] = useState<StudentPointDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setSaved(false);
    setMoreOpen(false);
    loadPointDetail(nodeId)
      .then((payload) => {
        if (!cancelled) setDetail(payload);
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
  }, [loadPointDetail, nodeId]);

  const video = detail?.videos[0] || null;
  const principleText =
    detail?.principle_mode === "equation"
      ? buildReactionEquationRows({
          equations: detail.reaction_equations,
          legacyText: detail.principle_equation,
          presentation: "studentMobile",
          filterInvalid: true,
        })
          .map((row) => [row.fallback, row.annotation ? `补充说明：${row.annotation}` : ""].filter(Boolean).join("\n"))
          .filter(Boolean)
          .join("\n")
      : detail?.principle_text;
  const pathText = detail ? catalogPathLabel(detail.breadcrumbs) : search.catalogPath || "";
  const assistantContext = useMemo<AssistantContext | null>(() => {
    if (!detail) return null;
    const path = detail.assessment_context.catalog_path.map((item) => item.title).filter(Boolean);
    return {
      context_type: "learning_point",
      context_title: detail.title,
      context_summary: compactText([
        path.length ? `目录路径：${path.join(" / ")}` : null,
        principleText ? `实验原理：${principleText}` : null,
        detail.phenomenon_explanation ? `现象解释：${detail.phenomenon_explanation}` : null,
        detail.safety_note ? `安全提示：${detail.safety_note}` : null,
      ]),
      chapter_id: detail.chapter_id,
      point_node_id: detail.assessment_context.point_node_id,
      source_node_id: detail.assessment_context.source_node_id || detail.source_node_id || null,
      catalog_path: path,
      prompts: ["这个点位主要观察什么？", "解释这个现象背后的化学原理", "学习这个点位要注意哪些安全事项？"],
    };
  }, [detail, principleText]);

  return (
    <section className="learning-panel catalog-point-detail" aria-label="点位视频详情">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载点位详情" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {detail ? (
        <>
          <PointVideoPlayer
            src={video?.stream_path ? resolveMediaUrl(video.stream_path) : null}
            poster={video?.thumbnail_path ? resolveMediaUrl(video.thumbnail_path) : null}
            emptyReason={detail.no_video_reason}
            onBack={onBack}
          />

          <section className="catalog-point-summary">
            <p>{pathText}</p>
            <h2>{detail.title}</h2>
          </section>

          {!previewMode ? (
            <section className="point-title-actions" aria-label="点位操作">
              <div className="point-title-action-row">
                <button
                  type="button"
                  className="point-title-action primary"
                  disabled={!assistantEnabled || !assistantContext}
                  onClick={() => assistantContext && onOpenAssistant(assistantContext)}
                >
                  <Atom size={19} />
                  <span>问问Atom</span>
                </button>
                <button type="button" className="point-title-action" disabled={finishing} onClick={() => onFinishLearning(detail)}>
                  <ClipboardList size={19} />
                  <span>{finishing ? "生成中" : "测一测"}</span>
                </button>
                <button type="button" className={saved ? "point-title-action active" : "point-title-action"} onClick={() => setSaved((value) => !value)}>
                  <Bookmark size={19} />
                  <span>{saved ? "已收藏" : "收藏"}</span>
                </button>
                <button type="button" className={moreOpen ? "point-title-action active" : "point-title-action"} onClick={() => setMoreOpen((value) => !value)}>
                  <MoreHorizontal size={20} />
                  <span>更多</span>
                </button>
              </div>
              {finishError ? <div className="form-error">{finishError}</div> : null}
              {moreOpen ? (
                <div className="point-title-more-panel">
                  <span>反馈问题、分享给同学等低频操作后续放在这里。</span>
                </div>
              ) : null}
            </section>
          ) : null}

          <LearningContentSection title="现象解释" body={detail.phenomenon_explanation || ""} icon={<Eye size={18} />} className="phenomenon-section" />
          <PrincipleContentSection detail={detail} body={principleText || ""} />
          <LearningContentSection title="安全提示" body={detail.safety_note || ""} icon={<ShieldAlert size={18} />} className="safety-section" />

          <section className="detail-section related-point-section">
            <h3>相关实验链接</h3>
            {detail.related_points.length ? (
              <div className="related-point-list">
                {detail.related_points.map((item) => (
                  <button type="button" key={item.node_id} disabled={previewMode} onClick={() => onOpenRelatedPoint(item.node_id, item.title)}>
                    <span className="related-point-thumb" aria-hidden="true">
                      <PlayCircle size={22} />
                    </span>
                    <span className="related-point-copy">
                      <span>{item.title}</span>
                      <small>{item.relation_type || "相关实验"}</small>
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <MobileEmptyState className="empty-learning-card">暂无相关实验链接</MobileEmptyState>
            )}
          </section>

        </>
      ) : null}
    </section>
  );
}

function LearningContentSection({
  title,
  body,
  mode,
  icon,
  className = "",
}: {
  title: string;
  body: string;
  mode?: string;
  icon?: ReactNode;
  className?: string;
}) {
  const sectionClassName = [
    "detail-section",
    "point-learning-section",
    className,
    mode === "equation" ? "equation-mode" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={sectionClassName}>
      <h3>
        {icon}
        <span>{title}</span>
      </h3>
      {body ? <p>{body}</p> : <MobileEmptyState className="empty-learning-card">暂无内容</MobileEmptyState>}
    </section>
  );
}

function PrincipleContentSection({ detail, body }: { detail: StudentPointDetailResponse; body: string }) {
  if (detail.principle_mode !== "equation") {
    return <LearningContentSection title="实验原理" mode={detail.principle_mode} body={body} icon={<FlaskConical size={18} />} className="principle-section" />;
  }

  const rows = buildReactionEquationRows({
    equations: detail.reaction_equations,
    legacyText: detail.principle_equation,
    presentation: "studentMobile",
    filterInvalid: true,
  });

  return (
    <section className="detail-section point-learning-section principle-section equation-mode">
      <h3>
        <FlaskConical size={18} />
        <span>实验原理</span>
      </h3>
      {rows.length ? (
        <div className="point-equation-list">
          {rows.map((row, index) => (
              <div className="point-equation-row" key={row.key}>
                <span className="point-equation-index" aria-hidden="true">{index + 1}</span>
                <ChemEquation latex={row.latex} fallback={row.fallback} className="point-chem-equation" />
                {row.annotation ? (
                  <p className="point-equation-note">
                    {row.annotation}
                  </p>
                ) : null}
              </div>
          ))}
        </div>
      ) : (
        <MobileEmptyState className="empty-learning-card">暂无内容</MobileEmptyState>
      )}
    </section>
  );
}
