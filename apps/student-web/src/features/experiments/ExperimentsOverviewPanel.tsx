import { useEffect, useState } from "react";
import { ChevronRight, FlaskConical, LoaderCircle } from "lucide-react";
import { StudentLearningHomeResponse, errorMessage, getStudentLearningHome } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { stripExperimentPrefix } from "./experimentFormat";

export function ExperimentsOverviewPanel({ onSelectGroup }: { onSelectGroup: (parentCode: string) => void }) {
  const [home, setHome] = useState<StudentLearningHomeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentLearningHome()
      .then((payload) => {
        if (!cancelled) setHome(payload);
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
  }, []);

  return (
    <section className="learning-panel experiments-overview-panel" aria-label="实验资源">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载实验资源" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {home ? (
        <>
          <section className="resource-overview-card">
            <div>
              <p>实验资源</p>
              <h2>{home.groups.length} 个实验模块</h2>
              <span>
                {home.areas.filter((area) => area.enabled).length} 个学习区域 / {home.groups.reduce((total, group) => total + group.question_count, 0)} 道配套题
              </span>
            </div>
            <FlaskConical size={24} />
          </section>
          <div className="experiment-module-list">
            {home.groups.map((group) => (
              <button className={group.recommended ? "experiment-module-card recommended" : "experiment-module-card"} key={group.parent_code} type="button" onClick={() => onSelectGroup(group.parent_code)}>
                {group.recommended ? <em>推荐学习</em> : null}
                <div>
                  <p>{group.area_name}</p>
                  <h3>{stripExperimentPrefix(group.parent_title)}</h3>
                  <span>
                    {group.experiment_count} 个点位 / {group.published_video_count} 个视频 / {group.question_count} 道题
                  </span>
                </div>
                <ChevronRight size={18} />
              </button>
            ))}
          </div>
          {!home.groups.length ? (
            <MobileEmptyState className="empty-learning-card" icon={<FlaskConical size={20} />}>
              <span>暂无可学习的实验模块</span>
            </MobileEmptyState>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
