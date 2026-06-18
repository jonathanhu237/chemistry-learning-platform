import { ClipboardList } from "lucide-react";

export function AssessmentHomePanel() {
  return (
    <section className="learning-panel assessment-home-panel" aria-label="测评">
      <section className="tab-empty-card">
        <span className="panel-icon">
          <ClipboardList size={20} />
        </span>
        <div>
          <p>当前测评</p>
          <h2>完成章节学习后进入后测</h2>
          <span>后测会根据本次学习的实验点生成，完成后这里会显示报告和错题讲解。</span>
        </div>
      </section>
    </section>
  );
}
