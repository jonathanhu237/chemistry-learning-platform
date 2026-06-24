import { BookOpenCheck, ChevronRight } from "lucide-react";
import type { StudentLearningPageResponse } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { profileAreaIds, type AreaId } from "../periodic-table/periodicHelpers";
import { formatChapterEntryTitle } from "./learningFormat";

type LearningProfileSummary = StudentLearningPageResponse["profiles"][number];

export function learningProfilesForArea(selectedArea: AreaId, profiles: LearningProfileSummary[]): LearningProfileSummary[] {
  return profiles.filter((profile) => profileAreaIds(profile).includes(selectedArea));
}

export function LearningChapterEntryRows({
  profiles,
  onSelectProfile,
}: {
  profiles: LearningProfileSummary[];
  onSelectProfile: (profile: LearningProfileSummary) => void;
}) {
  return (
    <div className="chapter-card-list">
      {profiles.map((profile) => {
        const chapterEntryTitle = formatChapterEntryTitle(profile);
        return (
          <button
            aria-label={chapterEntryTitle}
            className="chapter-entry-card"
            key={profile.profile_id}
            type="button"
            onClick={() => onSelectProfile(profile)}
          >
            <div className="chapter-entry-title">
              <strong>{chapterEntryTitle}</strong>
            </div>
            <span className="chapter-entry-elements">{profile.element_symbols.join(" ") || profile.family_name}</span>
            <ChevronRight size={17} />
          </button>
        );
      })}
    </div>
  );
}

export function LearningAreaChapterList({
  selectedArea,
  profiles,
  onSelectProfile,
}: {
  selectedArea: AreaId;
  profiles: LearningProfileSummary[];
  onSelectProfile: (profile: LearningProfileSummary) => void;
}) {
  const selectedAreaProfiles = learningProfilesForArea(selectedArea, profiles);

  return (
    <section className="chapter-card-panel" aria-label="可学习章节">
      {selectedAreaProfiles.length ? (
        <LearningChapterEntryRows profiles={selectedAreaProfiles} onSelectProfile={onSelectProfile} />
      ) : (
        <MobileEmptyState className="empty-learning-card" icon={<BookOpenCheck size={20} />}>
          <span>暂无可学习章节</span>
        </MobileEmptyState>
      )}
    </section>
  );
}
