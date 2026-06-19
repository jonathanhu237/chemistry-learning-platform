import { useEffect, useState } from "react";
import { ClipboardList, FlaskConical, LoaderCircle, MessageCircle, Video } from "lucide-react";
import { StudentExperimentDetailResponse, errorMessage, getStudentExperimentDetail, studentMediaUrl } from "../../api";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { FinishLearningAction } from "../../shared/learning/FinishLearningAction";
import { LearningState } from "../../shared/mobile/LearningState";
import { PageBar } from "../../shared/mobile/PageBar";
import { compactText } from "../../shared/utils/text";
import type { ChapterLearningView } from "../../app/router/routeTypes";
import type { AssistantContext } from "../assistant/assistantContext";
import { stripExperimentPrefix } from "./experimentFormat";

export function ExperimentDetailPanel({
  experimentId,
  profileId,
  propertyKey,
  propertyTitle,
  elementSymbol,
  chapterView,
  pointKey,
  pointTitle,
  onBack,
  onFinishLearning,
  finishing,
  finishError,
  assistantEnabled,
  onOpenAssistant,
}: {
  experimentId: string;
  profileId?: string | null;
  propertyKey?: string | null;
  propertyTitle?: string | null;
  elementSymbol?: string | null;
  chapterView?: ChapterLearningView | null;
  pointKey?: string | null;
  pointTitle?: string | null;
  onBack: () => void;
  onFinishLearning: () => void;
  finishing: boolean;
  finishError: string;
  assistantEnabled: boolean;
  onOpenAssistant: (context: AssistantContext) => void;
}) {
  const [detail, setDetail] = useState<StudentExperimentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentExperimentDetail(experimentId)
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
  }, [experimentId]);

  const video = detail?.videos.find((item) => pointKey && item.point_key === pointKey) || detail?.videos[0] || null;
  const effectivePointTitle = pointTitle || video?.point_title || detail?.video_candidates[0] || detail?.title || "实验点位";
  const detailAssistantContext: AssistantContext | null = detail
    ? {
        context_type: "learning_point",
        context_title: effectivePointTitle,
        context_summary: compactText([
          chapterView ? `当前视图：${chapterView === "experiments" ? "实验视频" : "性质通识"}` : null,
          propertyTitle ? `相关性质：${propertyTitle}` : null,
          elementSymbol ? `当前元素：${elementSymbol}` : null,
          `实验：${detail.title}`,
          detail.summary || null,
          pointKey ? `点位标识：${pointKey}` : null,
          detail.video_candidates.length ? `观察点：${detail.video_candidates.join("、")}` : null,
          detail.videos.length ? `视频：${detail.videos.map((item) => item.point_title || item.title).join("、")}` : null,
        ]),
        chapter_id: detail.chapter_ids[0] || null,
        experiment_id: detail.id,
        point_key: pointKey || video?.point_key || detail.video_candidates[0] || null,
        prompts: ["这个现象说明什么？", "帮我解释反应原理", "这个实验怎么记？"],
      }
    : null;
  return (
    <section className="learning-panel" aria-label="实验详情">
      <PageBar title={effectivePointTitle} onBack={onBack} />
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载实验详情" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {detail ? (
        <>
          <section className="video-stage">
            {video?.stream_path ? (
              <video
                controls
                playsInline
                poster={video.thumbnail_path ? studentMediaUrl(video.thumbnail_path) : undefined}
                src={studentMediaUrl(video.stream_path)}
              />
            ) : (
              <div className="video-placeholder">
                <Video size={34} />
                <strong>实验视频待发布</strong>
              </div>
            )}
          </section>

          <section className="experiment-detail-card">
            <p>{propertyTitle || detail.module_title || detail.parent_title}</p>
            <h2>{effectivePointTitle}</h2>
            <small>{stripExperimentPrefix(detail.title)}</small>
            {detail.summary ? <span>{detail.summary}</span> : null}
          </section>

          <section className="detail-section">
            <h3>实验观察与相关点位</h3>
            {detail.video_candidates.length ? (
              <div className="candidate-list">
                {detail.video_candidates.map((candidate) => (
                  <div key={candidate}>
                    <FlaskConical size={16} />
                    <span>{candidate}</span>
                  </div>
                ))}
              </div>
            ) : (
              <MobileEmptyState className="empty-learning-card">暂无观察点</MobileEmptyState>
            )}
          </section>

          <section className="detail-section practice-strip">
            <div>
              <p>练习</p>
              <h3>{detail.question_count} 题</h3>
            </div>
            <button type="button" disabled>
              <ClipboardList size={17} />
              <span>暂未开放</span>
            </button>
          </section>
          {assistantEnabled && detailAssistantContext ? (
            <MobileButton className="secondary-action full context-assistant-action" type="button" variant="secondary" onClick={() => onOpenAssistant(detailAssistantContext)}>
              <MessageCircle size={18} />
              <span>带着这个点位去问答</span>
            </MobileButton>
          ) : null}
          <FinishLearningAction loading={finishing} error={finishError} onClick={onFinishLearning} />
        </>
      ) : null}
    </section>
  );
}
