import { useEffect, useRef, useState } from "react";
import { FlaskConical, LoaderCircle, ChevronRight } from "lucide-react";
import type { StudentExperimentGroupSummary, StudentLearningPageResponse, StudentLearningProfile, StudentLearningPropertySection } from "../../api";
import { errorMessage, getStudentLearningPage } from "../../api";
import type { ChapterLearningView } from "../../app/router/routeTypes";
import { LearningState } from "../../shared/mobile/LearningState";
import { stripExperimentPrefix } from "../experiments/experimentFormat";
import { LearningExperimentsView } from "./LearningExperimentsView";
import { LearningFactsView } from "./LearningFactsView";
import { chapterExperimentGroupsForProfile } from "./learningFormat";

export function LearningHomePanel({
  profileId,
  initialPropertyKey,
  initialElementSymbol,
  initialChapterView,
  onProfileLoaded,
  onSelectPoint,
  onFinishLearning,
  finishing,
  finishError,
}: {
  profileId?: string | null;
  initialPropertyKey?: string | null;
  initialElementSymbol?: string | null;
  initialChapterView?: ChapterLearningView | null;
  onProfileLoaded?: (profile: StudentLearningProfile) => void;
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
  onFinishLearning: () => void;
  finishing: boolean;
  finishError: string;
}) {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(profileId || null);
  const [selectedPropertyKey, setSelectedPropertyKey] = useState<string>(initialPropertyKey || "");
  const [selectedElementSymbol, setSelectedElementSymbol] = useState<string>(initialElementSymbol || "");
  const [activeChapterView, setActiveChapterView] = useState<ChapterLearningView>(initialChapterView || "facts");
  const chapterScrollPositions = useRef<Record<ChapterLearningView, number>>({ facts: 0, experiments: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setSelectedProfileId(profileId || null);
  }, [profileId]);

  useEffect(() => {
    if (initialPropertyKey) setSelectedPropertyKey(initialPropertyKey);
  }, [initialPropertyKey]);

  useEffect(() => {
    if (initialElementSymbol) setSelectedElementSymbol(initialElementSymbol);
  }, [initialElementSymbol]);

  useEffect(() => {
    if (initialChapterView) setActiveChapterView(initialChapterView);
  }, [initialChapterView]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentLearningPage(selectedProfileId)
      .then((payload) => {
        if (cancelled) return;
        setPage(payload);
        if (!selectedProfileId && payload.active_profile?.profile_id) {
          setSelectedProfileId(payload.active_profile.profile_id);
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
  }, [selectedProfileId]);

  const profile = page?.active_profile || null;
  useEffect(() => {
    if (profile) onProfileLoaded?.(profile);
  }, [profile, onProfileLoaded]);

  useEffect(() => {
    if (!profile) return;
    const keys = profile.property_sections.map((section) => section.key);
    const preferred = initialPropertyKey && keys.includes(initialPropertyKey) ? initialPropertyKey : selectedPropertyKey;
    if (!preferred || !keys.includes(preferred)) {
      setSelectedPropertyKey(keys[0] || "");
    }
  }, [profile, initialPropertyKey, selectedPropertyKey]);
  useEffect(() => {
    if (!profile) return;
    const symbols = profile.elements.map((element) => element.symbol);
    const preferred =
      initialElementSymbol && symbols.includes(initialElementSymbol)
        ? initialElementSymbol
        : selectedElementSymbol || profile.default_element_symbol || symbols[0] || "";
    if (!preferred || !symbols.includes(preferred)) {
      setSelectedElementSymbol(profile.default_element_symbol && symbols.includes(profile.default_element_symbol) ? profile.default_element_symbol : symbols[0] || "");
    }
  }, [profile, initialElementSymbol, selectedElementSymbol]);

  const changeChapterView = (nextView: ChapterLearningView) => {
    if (nextView === activeChapterView) return;
    chapterScrollPositions.current[activeChapterView] = window.scrollY;
    setActiveChapterView(nextView);
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: chapterScrollPositions.current[nextView] || 0, behavior: "auto" });
    });
  };

  const selectedSection =
    profile?.property_sections.find((section) => section.key === selectedPropertyKey) || profile?.property_sections[0] || null;
  const selectedElement =
    profile?.elements.find((element) => element.symbol === selectedElementSymbol) ||
    profile?.elements.find((element) => element.symbol === profile.default_element_symbol) ||
    profile?.elements[0] ||
    null;
  const chapterExperimentGroups = profile ? chapterExperimentGroupsForProfile(profile) : [];
  const relatedPointCount = chapterExperimentGroups.reduce((total, group) => total + group.points.length, 0);
  return (
    <section className="learning-panel" aria-label="实验学习">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载学习资源" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error && profile ? (
        <>
          <ChapterViewSwitcher activeView={activeChapterView} experimentCount={relatedPointCount} onChange={changeChapterView} />

          {activeChapterView === "facts" ? (
            <LearningFactsView
              profile={profile}
              elements={profile.elements}
              selectedElement={selectedElement}
              selectedSection={selectedSection}
              experimentCount={relatedPointCount}
              onSelectElement={setSelectedElementSymbol}
              onShowExperiments={() => changeChapterView("experiments")}
            />
          ) : (
            <LearningExperimentsView
              profile={profile}
              groups={chapterExperimentGroups}
              pointCount={relatedPointCount}
              elementSymbol={null}
              onSelectPoint={onSelectPoint}
              finishing={finishing}
              finishError={finishError}
              onFinishLearning={onFinishLearning}
            />
          )}
        </>
      ) : null}
    </section>
  );
}

function ChapterViewSwitcher({
  activeView,
  experimentCount,
  onChange,
}: {
  activeView: ChapterLearningView;
  experimentCount: number;
  onChange: (view: ChapterLearningView) => void;
}) {
  const options: { key: ChapterLearningView; label: string; count?: number }[] = [
    { key: "facts", label: "性质通识" },
    { key: "experiments", label: "实验视频", count: experimentCount },
  ];

  return (
    <div className="chapter-view-switcher" role="tablist" aria-label="章节学习视图">
      {options.map((option) => (
        <button
          key={option.key}
          type="button"
          role="tab"
          aria-selected={activeView === option.key}
          className={activeView === option.key ? "active" : ""}
          onClick={() => onChange(option.key)}
        >
          <span>{option.label}</span>
          {typeof option.count === "number" ? <em>{option.count}</em> : null}
        </button>
      ))}
    </div>
  );
}

export function LearningProfileTabs({
  page,
  activeProfileId,
  onSelectProfile,
}: {
  page: StudentLearningPageResponse | null;
  activeProfileId: string;
  onSelectProfile: (profileId: string) => void;
}) {
  const profiles = page?.profiles || [];
  if (profiles.length <= 1) return null;
  return (
    <div className="learning-profile-tabs" aria-label="学习章节">
      {profiles.map((profile) => (
        <button
          key={profile.profile_id}
          type="button"
          className={profile.profile_id === activeProfileId ? "active" : ""}
          onClick={() => onSelectProfile(profile.profile_id)}
        >
          <strong>{profile.family_number || profile.title}</strong>
          <span>{profile.element_symbols.join(" ") || profile.family_name}</span>
        </button>
      ))}
    </div>
  );
}

export function ExperimentGroupCard({
  group,
  selected,
  onSelect,
}: {
  group: StudentExperimentGroupSummary;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button className={selected ? "family-card active" : "family-card"} type="button" aria-pressed={selected} onClick={onSelect}>
      {group.recommended ? <em>推荐学习</em> : null}
      <strong>{stripExperimentPrefix(group.parent_title)}</strong>
      <small>
        {group.experiment_count} 个实验点 / {group.question_count} 题
      </small>
    </button>
  );
}
