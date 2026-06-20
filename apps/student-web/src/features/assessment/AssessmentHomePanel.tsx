import { ClipboardList } from "lucide-react";
import { MobileEmptyState } from "../../mobile/primitives";

export function AssessmentHomePanel() {
  return (
    <section className="learning-panel assessment-home-panel" aria-label="测评">
      <MobileEmptyState className="empty-learning-card assessment-empty-state" icon={<ClipboardList size={20} />}>
        <div>
          <strong>随时开始智能测评</strong>
          <small>系统会根据未测实验和掌握较薄弱的实验自动组卷。</small>
        </div>
      </MobileEmptyState>
    </section>
  );
}
