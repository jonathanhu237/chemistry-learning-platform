import { CheckCircleOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { Typography } from "antd";

import type { AIConfiguration } from "../../api/settings";
import { guardrailStatus } from "./monitoringMappers";

const { Text, Title } = Typography;

type GuardrailModuleProps = {
  policy?: AIConfiguration["student_ai_policy"];
};

const policyLayers = [
  { key: "scope", title: "课程范围", description: "课程外请求引导回无机化学学习", signal: "Scope" },
  { key: "experiment", title: "实验安全", description: "危险操作只讲原理和安全提醒", signal: "Safety" },
  { key: "assessment", title: "测验保护", description: "索要答案时只给思路提示", signal: "Assessment" },
  { key: "evidence", title: "平台资源", description: "资源存在性必须检索平台来源", signal: "Grounding" },
  { key: "course", title: "课程问答", description: "普通化学问题由模型回答，RAG 辅助", signal: "Answer" },
];

export function GuardrailModule({ policy }: GuardrailModuleProps) {
  const meta = guardrailStatus(policy);
  const outcomes = policy?.outcomes || [];
  const handled = outcomes.filter((item) => item.mode !== "normal_answer").reduce((sum, item) => sum + item.count, 0);
  const maxOutcome = Math.max(...outcomes.map((item) => item.count), 1);
  const decisionCount = policy?.recent_decision_count || 0;
  const invalidCount = policy?.invalid_decision_count || 0;
  const layerStatus = policy?.active ? "已启用" : "待配置";

  return (
    <section className="ai-monitor-module">
      <div className="ai-guardrail-command">
        <div className={`ai-guardrail-shield ai-guardrail-shield-${meta.tone}`}>
          <div className="ai-guardrail-radar" aria-hidden="true">
            <div className="ai-guardrail-radar-grid" />
            <div className="ai-guardrail-radar-sweep" />
            <div className="ai-guardrail-radar-pulse ai-guardrail-radar-pulse-one" />
            <div className="ai-guardrail-radar-pulse ai-guardrail-radar-pulse-two" />
            <SafetyCertificateOutlined />
          </div>
          <div className="ai-guardrail-shield-copy">
            <Text type="secondary">Guardrail Core</Text>
            <Title level={3}>{meta.label}</Title>
            <Text>学生提问进入模型前完成风险判定，命中风险时按策略拦截、提示或降级。</Text>
          </div>
        </div>

        <div className="ai-guardrail-operations">
          <div className="ai-guardrail-headline">
            <div>
              <Text className="eyebrow">Student AI Defense</Text>
              <Title level={3}>输入检查、策略判定、受控输出</Title>
              <Text type="secondary">
                普通课程问答允许模型回答，RAG 用作辅助；平台资源、安全实验和测验答案仍由护栏强约束。
              </Text>
            </div>
            <div className="ai-guardrail-version">
              <span>Policy</span>
              <strong>{policy?.version || "student-ai-policy-v1"}</strong>
            </div>
          </div>

          <div className="ai-guardrail-pipeline">
            {[
              { key: "input", label: "输入层", value: "学生提问" },
              { key: "gate", label: "判定层", value: policy?.model || "本地策略" },
              { key: "action", label: "处置层", value: "放行 / 提示 / 拒答" },
            ].map((stage, index) => (
              <div key={stage.key} className={`ai-guardrail-stage ${index === 1 ? "ai-guardrail-stage-active" : ""}`}>
                <span>{stage.label}</span>
                <strong>{stage.value}</strong>
                {index < 2 ? <i aria-hidden="true" /> : null}
              </div>
            ))}
          </div>

          <div className="ai-guardrail-metrics">
            <div className="ai-guardrail-metric">
              <Text type="secondary">近 24 小时判定</Text>
              <strong>{decisionCount}</strong>
              <span>实时日志</span>
            </div>
            <div className="ai-guardrail-metric ai-guardrail-metric-warn">
              <Text type="secondary">已处置风险</Text>
              <strong>{handled}</strong>
              <span>拒答 / 提示 / 兜底</span>
            </div>
            <div className="ai-guardrail-metric">
              <Text type="secondary">结构兜底</Text>
              <strong className={invalidCount ? "danger-text" : undefined}>{invalidCount}</strong>
              <span>异常输出保护</span>
            </div>
          </div>
        </div>
      </div>

      <div className="ai-guardrail-layers">
        {policyLayers.map((item, index) => (
          <div key={item.key} className="ai-policy-rail-item">
            <div className="ai-policy-rail-top">
              <span className="ai-policy-rail-index">{String(index + 1).padStart(2, "0")}</span>
              <span className="ai-policy-rail-signal">{item.signal}</span>
            </div>
            <div className="ai-policy-rail-content">
              <Text strong className="ai-policy-rail-title">{item.title}</Text>
              <Text type="secondary" className="ai-policy-rail-description">
                {item.description}
              </Text>
            </div>
            <div className="ai-policy-rail-status">
              <CheckCircleOutlined />
              <span>{layerStatus}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="ai-policy-outcome-panel">
        <div className="ai-policy-section-head">
          <Text strong>最近判定分布</Text>
          <Text type="secondary">本系统 Agent 日志</Text>
        </div>
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
          <div className="ai-policy-empty">暂无学生 AI 安全判定记录</div>
        )}
      </div>
    </section>
  );
}
