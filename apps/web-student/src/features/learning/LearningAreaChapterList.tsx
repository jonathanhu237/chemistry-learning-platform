import { Atom, ChevronRight } from "lucide-react";
import type { StudentLearningPageResponse } from "../../api";
import { MobileEmptyState } from "../../mobile/primitives";
import { profileAreaIds, type AreaId } from "../periodic-table/periodicHelpers";
import { formatChapterEntryTitle } from "./learningFormat";

type LearningProfileSummary = StudentLearningPageResponse["profiles"][number];

export function LearningAreaChapterList({
  selectedArea,
  profiles,
  onSelectProfile,
}: {
  selectedArea: AreaId;
  profiles: LearningProfileSummary[];
  onSelectProfile: (profile: LearningProfileSummary) => void;
}) {
  const selectedAreaProfiles = profiles.filter((profile) => profileAreaIds(profile).includes(selectedArea));

  return (
    <section className="chapter-card-panel" aria-label="可学习章节">
      {selectedAreaProfiles.length ? (
        <div className="chapter-card-list">
          {selectedAreaProfiles.map((profile) => {
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
      ) : (
        <MobileEmptyState className="empty-learning-card" icon={<Atom size={20} />}>
          <span>暂无可学习章节</span>
        </MobileEmptyState>
      )}
    </section>
  );
}
