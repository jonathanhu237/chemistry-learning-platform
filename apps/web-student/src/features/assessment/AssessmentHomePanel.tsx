import { ClipboardList } from "lucide-react";
import { MobileEmptyState } from "../../mobile/primitives";

export function AssessmentHomePanel() {
  return (
    <section className="learning-panel assessment-home-panel" aria-label="测评">
      <MobileEmptyState className="empty-learning-card assessment-empty-state" icon={<ClipboardList size={20} />}>
        <div>
          <strong>测评中心</strong>
          <small>可以自动组卷，也可以自己选择实验练习。</small>
        </div>
      </MobileEmptyState>
    </section>
  );
}
