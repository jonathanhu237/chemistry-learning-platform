import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { BookOpenCheck, FlaskConical, LoaderCircle } from "lucide-react";
import { navigateToChapter } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { StudentLearningPageResponse, errorMessage, getStudentLearningPage } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningAreaChapterList } from "../../features/learning/LearningAreaChapterList";
import { LearningState } from "../../shared/mobile/LearningState";
import { normalizeAreaId, periodicLegendLabelByAreaId } from "../../features/periodic-table/periodicHelpers";

export function LearningAreaPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { areaId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const selectedArea = normalizeAreaId(params.areaId);
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [loading, setLoading] = useState(Boolean(selectedArea));
  const [error, setError] = useState("");

  useEffect(() => {
    if (!selectedArea) {
      setPage(null);
      setLoading(false);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentLearningPage(null)
      .then((payload) => {
        if (!cancelled) setPage(payload);
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
  }, [selectedArea]);

  const profiles = page?.profiles || [];
  const title = selectedArea ? periodicLegendLabelByAreaId[selectedArea] : "学习选区";

  return (
    <DetailPageFrame title={title} source={search.from || "learn"}>
      <section className="learning-panel" aria-label="元素周期表选区章节">
        {!selectedArea ? (
          <MobileEmptyState className="empty-learning-card" icon={<BookOpenCheck size={20} />}>
            <span>这个学习选区暂不可用</span>
          </MobileEmptyState>
        ) : null}
        {selectedArea && loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载选区章节" /> : null}
        {selectedArea && error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
        {selectedArea && !loading && !error ? (
          <LearningAreaChapterList
            selectedArea={selectedArea}
            profiles={profiles}
            onSelectProfile={(profile) => {
              navigateToChapter(navigate, profile.profile_id, { from: "learn" });
            }}
          />
        ) : null}
      </section>
    </DetailPageFrame>
  );
}
