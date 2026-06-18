import { useEffect, useMemo, useState } from "react";
import { Atom, ChevronRight, FlaskConical, LoaderCircle } from "lucide-react";
import { StudentLearningPageResponse, errorMessage, getStudentLearningPage } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { PeriodicTable } from "../periodic-table/PeriodicTable";
import { periodicAreaByAreaId, profileAreaId, type AreaId } from "../periodic-table/periodicHelpers";
import { formatChapterEntryTitle, formatRecommendedAreaCueLabel } from "./learningFormat";

export function LearningEntryPanel({
  onSelectProfile,
}: {
  onSelectProfile: (profileId: string) => void;
}) {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedArea, setSelectedArea] = useState<AreaId>("p");

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
  const recommendedElementSymbols = useMemo(
    () => new Set<string>(recommendedProfile?.element_symbols || []),
    [recommendedProfile],
  );
  const selectedAreaProfiles = useMemo(
    () => profiles.filter((profile) => profileAreaId(profile) === selectedArea),
    [profiles, selectedArea],
  );
  const selectedAreaLearnableSymbols = useMemo(() => {
    const symbols = new Set<string>();
    selectedAreaProfiles.forEach((profile) => {
      profile.element_symbols.forEach((symbol) => symbols.add(symbol));
    });
    return symbols;
  }, [selectedAreaProfiles]);
  useEffect(() => {
    if (recommendedArea) setSelectedArea(recommendedArea);
  }, [recommendedArea]);

  return (
    <section className="learning-panel" aria-label="元素周期表章节入口">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载学习章节" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error ? (
        <>
          <section className="chapter-entry-hero">
            <p>元素周期表</p>
            <h2>选择本次学习的元素族</h2>
            <span>先从周期表定位章节，再进入该族的元素特性、通性规律和实验点位学习。</span>
          </section>

          <PeriodicTable
            selectedArea={selectedArea}
            recommendedArea={recommendedArea}
            recommendedCueLabel={recommendedCueLabel}
            recommendedSymbols={recommendedElementSymbols}
            learnableSymbols={selectedAreaLearnableSymbols}
            onSelectArea={setSelectedArea}
          />

          <section className="chapter-card-panel" aria-label="可学习章节">
            <div className="point-list-head">
              <div>
                <p>当前选区</p>
                <h2>{periodicAreaByAreaId[selectedArea]}</h2>
              </div>
              <span>{selectedAreaProfiles.length} 个</span>
            </div>
            {selectedAreaProfiles.length ? (
              <div className="chapter-card-list">
                {selectedAreaProfiles.map((profile) => {
                  const isRecommended = profile.profile_id === recommendedProfileId;
                  const chapterEntryTitle = formatChapterEntryTitle(profile);
                  return (
                    <button
                      aria-label={`${chapterEntryTitle}${isRecommended ? "，推荐学习" : ""}`}
                      className={isRecommended ? "chapter-entry-card recommended" : "chapter-entry-card"}
                      key={profile.profile_id}
                      type="button"
                      onClick={() => onSelectProfile(profile.profile_id)}
                    >
                      <div className="chapter-entry-title">
                        <strong>{chapterEntryTitle}</strong>
                      </div>
                      {isRecommended ? <em>推荐学习</em> : null}
                      <span className="chapter-entry-elements">{profile.element_symbols.join(" ") || profile.family_name}</span>
                      <ChevronRight size={17} />
                    </button>
                  );
                })}
              </div>
            ) : (
              <MobileEmptyState className="empty-learning-card" icon={<Atom size={20} />}>
                <span>暂无可学习章节</span>
              </MobileEmptyState>
            )}
          </section>

        </>
      ) : null}
    </section>
  );
}
