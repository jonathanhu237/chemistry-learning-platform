import { FlaskConical } from "lucide-react";
import type { StudentLearningChapterExperimentGroup, StudentLearningPointGroup, StudentLearningProfile } from "../../api";
import type { ChapterLearningView } from "../../app/router/routeTypes";
import { MobileEmptyState } from "../../mobile/primitives";
import { FinishLearningAction } from "../../shared/learning/FinishLearningAction";
import { LearningPointGroupView } from "./LearningPointGroupView";

export function LearningExperimentsView({
  profile,
  groups,
  pointCount,
  elementSymbol,
  onSelectPoint,
  finishing,
  finishError,
  onFinishLearning,
}: {
  profile: StudentLearningProfile;
  groups: StudentLearningChapterExperimentGroup[];
  pointCount: number;
  elementSymbol?: string | null;
  onSelectPoint: (point: {
    profileId: string;
    propertyKey: string;
    propertyTitle: string;
    elementSymbol?: string | null;
    chapterView?: ChapterLearningView;
    experimentId: string;
    pointKey?: string | null;
    pointTitle?: string | null;
  }) => void;
  finishing: boolean;
  finishError: string;
  onFinishLearning: () => void;
}) {
  return (
    <div className="chapter-view-panel experiments-view" data-view="experiments">
      <section className="point-list-panel">
        <div className="point-list-head">
          <div>
            <p>{profile.subtitle || profile.family_name || "视频与点位"}</p>
            <h2>实验-点位视频</h2>
          </div>
          <span>{pointCount} 个</span>
        </div>
        {groups.length ? (
          <div className="point-group-stack">
            {groups.map((group) => (
              <LearningPointGroupView
                key={group.parent_code || group.parent_title}
                group={group}
                profile={profile}
                onSelectPoint={onSelectPoint}
                elementSymbol={elementSymbol}
              />
            ))}
          </div>
        ) : (
          <MobileEmptyState className="empty-learning-card" icon={<FlaskConical size={20} />}>
            <span>该章节暂未匹配到开放实验点</span>
          </MobileEmptyState>
        )}
      </section>
      <FinishLearningAction loading={finishing} error={finishError} onClick={onFinishLearning} />
    </div>
  );
}
