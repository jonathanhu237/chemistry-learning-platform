import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { ClipboardList, FlaskConical, LoaderCircle, MessageCircle, ShieldAlert, Video } from "lucide-react";

import type { StudentPointDetailResponse } from "../../api";
import { errorMessage, getStudentCatalogPointDetail, studentMediaUrl } from "../../api";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { FinishLearningAction } from "../../shared/learning/FinishLearningAction";
import { LearningState } from "../../shared/mobile/LearningState";
import { PageBar } from "../../shared/mobile/PageBar";
import { compactText } from "../../shared/utils/text";
import type { AssistantContext } from "../assistant/assistantContext";
import { catalogPathLabel } from "./CatalogNodeCards";

function studentEquationDisplayText(equation: NonNullable<StudentPointDetailResponse["reaction_equations"]>[number]): string {
  const core = equation.canonical_display || equation.equation_core || equation.raw_text;
  const annotation = equation.annotation_text?.trim();
  return [core, annotation ? `补充说明：${annotation}` : ""].filter(Boolean).join("\n");
}

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

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
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
      ? (detail.reaction_equations || [])
          .filter((equation) => equation.validation_status !== "invalid")
          .map((equation) => studentEquationDisplayText(equation))
          .filter(Boolean)
          .join("\n") || detail.principle_equation
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
      <PageBar title={detail?.title || search.pointTitle || "点位详情"} onBack={onBack} />
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载点位详情" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {detail ? (
        <>
          <section className="video-stage">
            {video?.stream_path ? (
              <video
                controls
                playsInline
                poster={video.thumbnail_path ? resolveMediaUrl(video.thumbnail_path) : undefined}
                src={resolveMediaUrl(video.stream_path)}
              />
            ) : (
              <div className="video-placeholder">
                <Video size={34} />
                <strong>暂无可播放视频</strong>
                <span>{detail.no_video_reason || "老师发布点位内容后，可继续补充绑定视频。"}</span>
              </div>
            )}
          </section>

          <section className="experiment-detail-card catalog-point-summary">
            <p>{pathText}</p>
            <h2>{detail.title}</h2>
          </section>

          <LearningContentSection title="实验原理" mode={detail.principle_mode} body={principleText || ""} />
          <LearningContentSection title="现象解释" body={detail.phenomenon_explanation || ""} />
          <LearningContentSection title="安全提示" body={detail.safety_note || ""} icon={<ShieldAlert size={18} />} />

          <section className="detail-section related-point-section">
            <h3>相关实验链接</h3>
            {detail.related_points.length ? (
              <div className="related-point-list">
                {detail.related_points.map((item) => (
                  <button type="button" key={item.node_id} disabled={previewMode} onClick={() => onOpenRelatedPoint(item.node_id, item.title)}>
                    <span>{item.title}</span>
                    {item.relation_type ? <small>{item.relation_type}</small> : null}
                  </button>
                ))}
              </div>
            ) : (
              <MobileEmptyState className="empty-learning-card">暂无相关实验链接</MobileEmptyState>
            )}
          </section>

          {!previewMode ? (
          <section className="detail-section practice-strip">
            <div>
              <p>固定练习入口</p>
              <h3>{detail.assessment_context.point_node_id}</h3>
            </div>
            <button type="button" disabled={finishing} onClick={() => onFinishLearning(detail)}>
              <ClipboardList size={17} />
              <span>开始练习</span>
            </button>
          </section>
          ) : null}

          {!previewMode && assistantEnabled && assistantContext ? (
            <MobileButton className="secondary-action full context-assistant-action" type="button" variant="secondary" onClick={() => onOpenAssistant(assistantContext)}>
              <MessageCircle size={18} />
              <span>带着这个点位问 AI</span>
            </MobileButton>
          ) : null}
          {!previewMode ? <FinishLearningAction loading={finishing} error={finishError} onClick={() => onFinishLearning(detail)} /> : null}
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
}: {
  title: string;
  body: string;
  mode?: string;
  icon?: ReactNode;
}) {
  return (
    <section className={mode === "equation" ? "detail-section principle-section equation-mode" : "detail-section principle-section"}>
      <h3>
        {icon}
        <span>{title}</span>
      </h3>
      {body ? <p>{body}</p> : <MobileEmptyState className="empty-learning-card">暂无内容</MobileEmptyState>}
    </section>
  );
}
