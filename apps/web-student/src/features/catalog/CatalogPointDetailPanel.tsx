import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Atom, Bookmark, ClipboardList, Eye, FlaskConical, LoaderCircle, PlayCircle, ShieldAlert } from "lucide-react";

import { buildReactionEquationRows } from "../../../../shared/reactionEquations";
import type { StudentPointDetailResponse, StudentPointVideo, StudentVideoSaveRequest, StudentVideoSaveResponse } from "../../api";
import { errorMessage, getStudentCatalogPointDetail, removeStudentVideoSave, saveStudentVideo, studentMediaUrl } from "../../api";
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
  const [actionStatus, setActionStatus] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setSaved(false);
    setActionStatus("");
    loadPointDetail(nodeId)
      .then((payload) => {
        if (!cancelled) {
          setDetail(payload);
          setSaved(Boolean(payload.personal_state.favorite));
        }
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
  const subtitleTracks = useMemo(
    () =>
      (video?.subtitle_tracks || [])
        .filter((track) => track.stream_path)
        .map((track) => ({
          id: track.id,
          kind: track.kind,
          language_code: track.language_code,
          label: track.label,
          is_default: track.is_default,
          streamUrl: resolveMediaUrl(track.stream_path),
        })),
    [resolveMediaUrl, video],
  );
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

  const applySaveResponse = useCallback((response: StudentVideoSaveResponse) => {
    setSaved(response.personal_state.favorite);
    setDetail((current) =>
      current
        ? {
            ...current,
            personal_state: response.personal_state,
          }
        : current,
    );
  }, []);

  const buildSavePayload = useCallback((targetDetail: StudentPointDetailResponse, targetVideo: StudentPointVideo, source: string): StudentVideoSaveRequest => {
    return {
      placement_node_id: targetDetail.placement_node_id || targetDetail.node_id,
      canonical_point_id: targetDetail.canonical_point_id,
      media_id: targetVideo.media_id,
      source,
    };
  }, []);

  const toggleFavorite = useCallback(() => {
    if (!detail || !video) {
      setActionStatus("当前实验还没有可收藏的视频");
      return;
    }
    const active = saved;
    const request = active
      ? removeStudentVideoSave("favorite", buildSavePayload(detail, video, "point_detail"))
      : saveStudentVideo("favorite", buildSavePayload(detail, video, "point_detail"));
    void request
      .then((response) => {
        applySaveResponse(response);
        setActionStatus(active ? `已取消收藏：${detail.title}` : `已收藏：${detail.title}`);
      })
      .catch((requestError) => setActionStatus(errorMessage(requestError)));
  }, [applySaveResponse, buildSavePayload, detail, saved, video]);

  return (
    <section className="learning-panel catalog-point-detail" aria-label="点位视频详情">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载点位详情" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {detail ? (
        <>
          <PointVideoPlayer
            src={video?.stream_path ? resolveMediaUrl(video.stream_path) : null}
            poster={video?.thumbnail_path ? resolveMediaUrl(video.thumbnail_path) : null}
            subtitleTracks={subtitleTracks}
            emptyReason={detail.no_video_reason}
            onBack={onBack}
          />

          <section className="catalog-point-summary">
            <p>{pathText}</p>
            <h2>{detail.title}</h2>
          </section>

          <LearningContentSection title="现象解释" body={detail.phenomenon_explanation || ""} icon={<Eye size={18} />} className="phenomenon-section" />
          <PrincipleContentSection detail={detail} body={principleText || ""} />
          <LearningContentSection title="安全提示" body={detail.safety_note || ""} icon={<ShieldAlert size={18} />} className="safety-section" />

          {!previewMode ? (
            <section className="point-learning-actions" aria-label="学习操作">
              <div className="point-learning-main-row">
                <button
                  type="button"
                  className="point-learning-main-action primary"
                  disabled={finishing}
                  onClick={() => onFinishLearning(detail)}
                >
                  <ClipboardList size={20} />
                  <span>{finishing ? "生成中" : "学完测一测"}</span>
                </button>
                <button
                  type="button"
                  className="point-learning-main-action"
                  disabled={!assistantEnabled || !assistantContext}
                  onClick={() => assistantContext && onOpenAssistant(assistantContext)}
                >
                  <Atom size={20} />
                  <span>问问Atom</span>
                </button>
              </div>
              <div className="point-learning-utility-row" aria-label="次要操作">
                <button
                  type="button"
                  className={saved ? "point-learning-utility-action active" : "point-learning-utility-action"}
                  aria-label={saved ? "取消收藏" : "收藏"}
                  aria-pressed={saved}
                  onClick={toggleFavorite}
                >
                  <Bookmark size={18} />
                  <span>{saved ? "已收藏" : "收藏"}</span>
                </button>
              </div>
              {finishError ? <div className="form-error">{finishError}</div> : null}
              {actionStatus ? <div className="point-learning-action-hint">{actionStatus}</div> : null}
            </section>
          ) : null}

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
                      <small>{relatedPointRelationLabel(item.relation_type)}</small>
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

function relatedPointRelationLabel(relationType?: string | null) {
  switch (relationType) {
    case "default":
    case "default_override":
    case "generated_default":
      return "推荐实验";
    case "manual":
    default:
      return "相关实验";
  }
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
