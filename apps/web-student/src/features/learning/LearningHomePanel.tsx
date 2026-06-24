import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import { BookOpenCheck, ChevronRight, FlaskConical, LoaderCircle } from "lucide-react";
import type { StudentLearningElementBadge, StudentLearningPageResponse, StudentLearningProfile } from "../../api";
import { errorMessage, getStudentLearningPage } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { ElementTileContent } from "../periodic-table/PeriodicElementCell";
import { elementEnglishName, elementTileStyle } from "../periodic-table/periodicHelpers";
import { LearningElementChips } from "./LearningElementChips";

export function LearningHomePanel({
  profileId,
  initialElementSymbol,
  onProfileLoaded,
  onOpenElementDetail,
}: {
  profileId?: string | null;
  initialElementSymbol?: string | null;
  onProfileLoaded?: (profile: StudentLearningProfile) => void;
  onOpenElementDetail: (profileId: string, symbol: string) => void;
}) {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(profileId || null);
  const [selectedElementSymbol, setSelectedElementSymbol] = useState<string>(initialElementSymbol || "");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setSelectedProfileId(profileId || null);
  }, [profileId]);

  useEffect(() => {
    if (initialElementSymbol) setSelectedElementSymbol(initialElementSymbol);
  }, [initialElementSymbol]);

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
    const symbols = profile.elements.map((element) => element.symbol);
    const preferred =
      initialElementSymbol && symbols.includes(initialElementSymbol)
        ? initialElementSymbol
        : selectedElementSymbol || profile.default_element_symbol || symbols[0] || "";
    if (!preferred || !symbols.includes(preferred)) {
      setSelectedElementSymbol(profile.default_element_symbol && symbols.includes(profile.default_element_symbol) ? profile.default_element_symbol : symbols[0] || "");
    }
  }, [profile, initialElementSymbol, selectedElementSymbol]);

  const selectedElement = useMemo(() => {
    if (!profile) return null;
    return (
      profile.elements.find((element) => element.symbol === selectedElementSymbol) ||
      profile.elements.find((element) => element.symbol === profile.default_element_symbol) ||
      profile.elements[0] ||
      null
    );
  }, [profile, selectedElementSymbol]);
  const catalogHintCount = profile?.property_sections.length || 0;

  return (
    <section className="learning-panel" aria-label="章节学习">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载学习内容" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error && !profile ? (
        <MobileEmptyState className="empty-learning-card" icon={<BookOpenCheck size={20} />}>
          <span>没有找到学习章节</span>
        </MobileEmptyState>
      ) : null}
      {!loading && !error && profile ? (
        <>
          <LearningElementChips
            elements={profile.elements}
            activeSymbol={selectedElement?.symbol || ""}
            onSelectElement={setSelectedElementSymbol}
          />
          {selectedElement ? (
            <ChapterElementSummary
              profile={profile}
              element={selectedElement}
              catalogHintCount={catalogHintCount}
              onOpenDetail={() => onOpenElementDetail(profile.profile_id, selectedElement.symbol)}
            />
          ) : null}
        </>
      ) : null}
    </section>
  );
}

function ChapterElementSummary({
  profile,
  element,
  catalogHintCount,
  onOpenDetail,
}: {
  profile: StudentLearningProfile;
  element: StudentLearningElementBadge;
  catalogHintCount: number;
  onOpenDetail: () => void;
}) {
  const familyLabel = profile.family_name || profile.title;
  const location = [
    element.group_label || element.group,
    typeof element.period === "number" ? `${element.period}周期` : "",
    element.block ? `${element.block}区` : "",
  ]
    .filter(Boolean)
    .join(" / ");
  const focus = element.card_focus || (element.common_valence ? `常见价态 ${element.common_valence}` : "核心性质待补充");
  const relevance = element.card_relevance || "查看详情了解它在本章实验中的作用。";
  const tags = compactElementTags(
    element.card_tags?.length ? element.card_tags : fallbackElementTags(element, location || familyLabel),
  );
  const catalogEntryLabel = catalogHintCount > 0 ? `${catalogHintCount} 个目录主题` : "目录待补充";

  return (
    <section
      className="chapter-element-summary"
      style={elementTileStyle(element) as CSSProperties}
      aria-label={`${element.name}元素摘要`}
    >
      <div className="chapter-element-summary-head">
        <div className="selected-element-symbol chapter-element-summary-symbol" style={elementTileStyle(element)}>
          <ElementTileContent element={element} />
        </div>
        <div className="chapter-element-summary-copy">
          <p>当前观察元素</p>
          <h2>
            {element.name} <span>{elementEnglishName(element)}</span>
          </h2>
          <strong className="chapter-element-summary-focus">{focus}</strong>
          <span className="chapter-element-summary-relevance">{relevance}</span>
        </div>
      </div>
      <div className="chapter-element-summary-foot">
        {tags.map((tag) => (
          <small key={tag}>{tag}</small>
        ))}
        <small>{catalogEntryLabel}</small>
      </div>
      <button className="chapter-element-detail-action" type="button" onClick={onOpenDetail}>
        <span>查看元素详情</span>
        <ChevronRight size={18} />
      </button>
    </section>
  );
}

function fallbackElementTags(element: StudentLearningElementBadge, location: string): string[] {
  return [
    location,
    element.state_at_20c || element.state || "",
    element.common_valence ? `常见${element.common_valence}价` : "",
  ];
}

function compactElementTags(tags: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const tag of tags) {
    const text = tag.trim();
    if (!text || seen.has(text)) continue;
    seen.add(text);
    result.push(text);
    if (result.length >= 3) break;
  }
  return result;
}
