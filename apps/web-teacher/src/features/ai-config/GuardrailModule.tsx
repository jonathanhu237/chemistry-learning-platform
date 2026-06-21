import { SafetyCertificateOutlined } from "@ant-design/icons";
import { Tag, Typography } from "antd";

import type { AIConfiguration } from "../../api/settings";
import { guardrailStatus } from "./monitoringMappers";
import { MetricGrid, MetricTile, ModuleHeader } from "./MonitoringShared";

const { Text } = Typography;

type GuardrailModuleProps = {
  policy?: AIConfiguration["student_ai_policy"];
};

const policyLayers = [
  { key: "scope", title: "课程范围", signal: "Scope" },
  { key: "experiment", title: "实验安全", signal: "Safety" },
  { key: "assessment", title: "测验保护", signal: "Assessment" },
  { key: "evidence", title: "平台资源", signal: "Grounding" },
  { key: "course", title: "课程问答", signal: "Answer" },
];

export function GuardrailModule({ policy }: GuardrailModuleProps) {
  const meta = guardrailStatus(policy);
  const outcomes = policy?.outcomes || [];
  const handled = outcomes.filter((item) => item.mode !== "normal_answer").reduce((sum, item) => sum + item.count, 0);
  const maxOutcome = Math.max(...outcomes.map((item) => item.count), 1);

  return (
    <section className="ai-monitor-module">
      <ModuleHeader
        eyebrow="Student AI Defense"
        title={meta.label}
        description="学生提问进入模型前完成风险判定，命中风险时按策略拦截、提示或降级。"
        status={meta.label}
        tone={meta.tone}
      />
      <MetricGrid>
        <MetricTile label="Policy" value={policy?.version || "student-ai-policy-v1"} />
        <MetricTile label="判定模型" value={policy?.model || "本地策略"} />
        <MetricTile label="近 24 小时判定" value={policy?.recent_decision_count || 0} />
        <MetricTile label="已处置风险" value={handled} tone={handled ? "warn" : "good"} />
        <MetricTile label="结构兜底" value={policy?.invalid_decision_count || 0} tone={policy?.invalid_decision_count ? "warn" : "good"} />
        <MetricTile label="启用状态" value={policy?.active ? "已启用" : "未启用"} tone={policy?.active ? "good" : "idle"} />
      </MetricGrid>
      <div className="ai-monitor-two-column">
        <section className="ai-monitor-subpanel">
          <h3>护栏覆盖</h3>
          <div className="ai-monitor-policy-grid">
            {policyLayers.map((item) => (
              <div key={item.key}>
                <SafetyCertificateOutlined />
                <strong>{item.title}</strong>
                <Tag>{item.signal}</Tag>
              </div>
            ))}
          </div>
        </section>
        <section className="ai-monitor-subpanel">
          <h3>最近判定分布</h3>
          {outcomes.length ? (
            <div className="ai-policy-outcomes">
              {outcomes.map((item) => (
                <div key={item.mode} className="ai-policy-outcome">
                  <div>
                    <span>{item.label}</span>
                    <div className="ai-policy-outcome-track">
                      <i style={{ width: `${Math.max(8, Math.round((item.count / maxOutcome) * 100))}%` }} />
                    </div>
                  </div>
                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          ) : (
            <Text type="secondary">暂无学生 AI 安全判定记录</Text>
          )}
        </section>
      </div>
    </section>
  );
}
