import { FlaskConical, PlayCircle } from "lucide-react";
import type { StudentLearningChapterExperimentGroup, StudentLearningPointCard, StudentLearningPointGroup, StudentLearningProfile } from "../../api";
import { studentMediaUrl } from "../../api";
import { stripExperimentPrefix } from "../experiments/experimentFormat";

export function LearningPointGroupView({
  group,
  profile,
  elementSymbol,
  onSelectPoint,
}: {
  group: StudentLearningChapterExperimentGroup | StudentLearningPointGroup;
  profile: StudentLearningProfile;
  elementSymbol?: string | null;
  onSelectPoint: (point: {
    profileId: string;
    propertyKey: string;
    propertyTitle: string;
    elementSymbol?: string | null;
    experimentId: string;
    pointKey?: string | null;
    pointTitle?: string | null;
  }) => void;
}) {
  return (
    <section className="point-group">
      <div className="point-group-title">
        <FlaskConical size={17} />
        <strong>{stripExperimentPrefix(group.parent_title)}</strong>
      </div>
      <div className="point-card-grid">
        {group.points.map((point) => (
          <LearningPointCardView
            key={`${point.id}-${point.property_key}-${point.point_key || point.title}`}
            point={point}
            profile={profile}
            elementSymbol={elementSymbol}
            onSelectPoint={onSelectPoint}
          />
        ))}
      </div>
    </section>
  );
}

function LearningPointCardView({
  point,
  profile,
  elementSymbol,
  onSelectPoint,
}: {
  point: StudentLearningPointCard;
  profile: StudentLearningProfile;
  elementSymbol?: string | null;
  onSelectPoint: (point: {
    profileId: string;
    propertyKey: string;
    propertyTitle: string;
    elementSymbol?: string | null;
    experimentId: string;
    pointKey?: string | null;
    pointTitle?: string | null;
  }) => void;
}) {
  const video = point.videos[0] || null;
  return (
    <button
      className="learning-point-card"
      type="button"
      onClick={() =>
        onSelectPoint({
          profileId: profile.profile_id,
          propertyKey: point.property_key,
          propertyTitle: point.property_title,
          elementSymbol,
          experimentId: point.id,
          pointKey: point.point_key,
          pointTitle: point.point_title || point.title,
        })
      }
    >
      <div className="point-thumb">
        {video?.thumbnail_path ? <img src={studentMediaUrl(video.thumbnail_path)} alt="" /> : <PlayCircle size={30} />}
        <span>{point.code}</span>
      </div>
      <div className="point-card-copy">
        <p>{point.point_title || point.property_title}</p>
        <h3>{stripExperimentPrefix(point.title)}</h3>
        {point.formula || point.summary ? <small>{point.formula || point.summary}</small> : null}
        <span>
          视频 {point.published_video_count || point.video_candidate_count} / 练习 {point.question_count}
        </span>
      </div>
    </button>
  );
}
