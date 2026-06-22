import { useEffect, useState } from "react";
import { ArrowRight, FlaskConical, LoaderCircle, Sparkles } from "lucide-react";
import { StudentLearningPageResponse, errorMessage, getStudentLearningPage } from "../../api";
import { LearningState } from "../../shared/mobile/LearningState";
import { PeriodicTable } from "../periodic-table/PeriodicTable";
import { periodicAreaByAreaId, profileAreaId, type AreaId } from "../periodic-table/periodicHelpers";
import { LearningAreaPopover } from "./LearningAreaPopover";
import { formatChapterEntryTitle, formatRecommendedAreaCueLabel } from "./learningFormat";

type LearningProfileSummary = StudentLearningPageResponse["profiles"][number];

export function LearningEntryPanel({
  onSelectProfile,
}: {
  onSelectProfile: (profile: LearningProfileSummary) => void;
}) {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedArea, setSelectedArea] = useState<AreaId | null>(null);
  const [areaAnchorElement, setAreaAnchorElement] = useState<HTMLElement | null>(null);

  useEffect(() => {
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
  }, []);

  const profiles = page?.profiles || [];
  const recommendedProfileId = page?.recommended_profile_id || page?.active_profile?.profile_id || profiles[0]?.profile_id || "";
  const recommendedProfile = profiles.find((profile) => profile.profile_id === recommendedProfileId) || profiles[0] || null;
  const recommendedArea = recommendedProfile ? profileAreaId(recommendedProfile) : null;
  const recommendedCueLabel = formatRecommendedAreaCueLabel(recommendedProfile);
  const recommendedAreaLabel = recommendedArea ? periodicAreaByAreaId[recommendedArea] : null;
  const closeAreaPopover = () => {
    setSelectedArea(null);
    setAreaAnchorElement(null);
  };

  return (
    <section className="learning-panel" aria-label="元素周期表章节入口">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载学习章节" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error ? (
        <>
          <PeriodicTable
            onSelectArea={(areaId, triggerElement) => {
              if (selectedArea === areaId && areaAnchorElement === triggerElement) {
                closeAreaPopover();
                return;
              }
              setSelectedArea(areaId);
              setAreaAnchorElement(triggerElement);
            }}
          />
          <LearningAreaPopover
            selectedArea={selectedArea}
            anchorElement={areaAnchorElement}
            open={Boolean(selectedArea && areaAnchorElement)}
            profiles={profiles}
            onOpenChange={(isOpen) => {
              if (!isOpen) closeAreaPopover();
            }}
            onSelectProfile={onSelectProfile}
          />
        </>
      ) : null}
      {!loading && !error && recommendedProfile ? (
        <button
          type="button"
          className="learning-recommendation-card"
          aria-label={`进入推荐学习 ${formatChapterEntryTitle(recommendedProfile)}`}
          onClick={() => onSelectProfile(recommendedProfile)}
        >
          <span className="learning-recommendation-kicker">
            <Sparkles size={15} />
            智能推荐
          </span>
          <strong>{formatChapterEntryTitle(recommendedProfile)}</strong>
          <small>
            {[recommendedAreaLabel || recommendedCueLabel, recommendedProfile.element_symbols.join(" ")]
              .filter(Boolean)
              .join(" · ")}
          </small>
          <span className="learning-recommendation-action">
            进入学习
            <ArrowRight size={16} />
          </span>
        </button>
      ) : null}
    </section>
  );
}
