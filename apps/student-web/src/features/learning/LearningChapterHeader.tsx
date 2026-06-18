import { Atom, MessageCircle } from "lucide-react";
import type { StudentLearningProfile } from "../../api";
import { MobileButton } from "../../mobile/primitives";
import type { AssistantContext } from "../assistant/assistantContext";

export function LearningChapterHeader({
  profile,
  onSwitchChapter,
  assistantContext,
  onOpenAssistant,
}: {
  profile: StudentLearningProfile;
  onSwitchChapter: () => void;
  assistantContext?: AssistantContext | null;
  onOpenAssistant: (context: AssistantContext) => void;
}) {
  return (
    <section className="chapter-context-card" aria-label="当前章节">
      <div className="chapter-context-copy">
        <div className="chapter-context-kicker">
          <p>当前章节</p>
          <span>{profile.hero.eyebrow || profile.subtitle || "元素性质"}</span>
        </div>
        <h2>{profile.title}</h2>
        <span>{profile.subtitle || profile.element_symbols.join(" ")}</span>
        <div className="chapter-context-summary">
          <strong>{profile.hero.title}</strong>
          {profile.hero.summary ? <small>{profile.hero.summary}</small> : null}
        </div>
      </div>
      <div className="chapter-context-actions">
        {assistantContext ? (
          <MobileButton className="chapter-switch-action" type="button" variant="ghost" fullWidth={false} onClick={() => onOpenAssistant(assistantContext)}>
            <MessageCircle size={17} />
            <span>问答</span>
          </MobileButton>
        ) : null}
        <MobileButton className="chapter-switch-action" type="button" variant="ghost" fullWidth={false} onClick={onSwitchChapter}>
          <Atom size={17} />
          <span>换章节</span>
        </MobileButton>
      </div>
    </section>
  );
}
