import { useEffect, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Flex,
  Form,
  Input,
  InputNumber,
  Select,
  Slider,
  Space,
  Switch,
  Tag,
  Typography,
} from "antd";

import type {
  AIConfiguration,
  AIConfigurationUpdate,
  CustomAssessmentSettings,
  LearningBehaviorSettings,
  PlatformSettingsResponse,
  SmartAssessmentSettings,
} from "../../api/settings";
import { api, putJson } from "../../api/http";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import "./settings.css";

const { Text } = Typography;

const defaultSmartAssessment: SmartAssessmentSettings = {
  enabled: true,
  question_count: 10,
  untested_ratio_percent: 20,
  weak_tendency_percent: 70,
  max_questions_per_experiment: 2,
  weak_curve: 2,
  weak_max_bonus: 9,
};

const questionCountOptions = [5, 10, 15, 20].map((value) => ({ label: `${value} 题`, value }));

const defaultCustomAssessment: CustomAssessmentSettings = {
  enabled: true,
  default_question_count: 10,
  max_question_count: 20,
  max_questions_per_experiment: 3,
};

function normalizeSmartAssessmentSettings(value: Partial<SmartAssessmentSettings> | undefined): SmartAssessmentSettings {
  const clean = Object.fromEntries(Object.entries(value || {}).filter(([, item]) => item !== undefined)) as Partial<SmartAssessmentSettings>;
  return { ...defaultSmartAssessment, ...clean };
}

function normalizeCustomAssessmentSettings(value: Partial<CustomAssessmentSettings> | undefined): CustomAssessmentSettings {
  const clean = Object.fromEntries(Object.entries(value || {}).filter(([, item]) => item !== undefined)) as Partial<CustomAssessmentSettings>;
  const merged = { ...defaultCustomAssessment, ...clean };
  return {
    ...merged,
    default_question_count: Math.min(merged.default_question_count, merged.max_question_count),
  };
}

function smartAssessmentTickets(settings: SmartAssessmentSettings, mastery: number) {
  const weakness = Math.max(0, Math.min(1, (100 - mastery) / 100));
  const weakBias = settings.weak_tendency_percent / 100;
  return 1 + weakBias * settings.weak_max_bonus * Math.pow(weakness, settings.weak_curve);
}

function SmartAssessmentCurve({ settings }: { settings: SmartAssessmentSettings }) {
  const data = [0, 20, 40, 60, 80, 100].map((mastery) => ({
    mastery,
    tickets: smartAssessmentTickets(settings, mastery),
  }));
  const maxTicket = Math.max(1, ...data.map((item) => item.tickets));
  const points = data
    .map((item, index) => {
      const x = 20 + index * 44;
      const y = 118 - (item.tickets / maxTicket) * 88;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <div className="smart-curve-preview" aria-label="掌握度抽题权重预览">
      <svg viewBox="0 0 260 146" role="img" aria-label="掌握度越低抽题票数越高">
        <line x1="20" y1="118" x2="240" y2="118" />
        <line x1="20" y1="30" x2="20" y2="118" />
        <polyline points={points} />
        {data.map((item, index) => {
          const x = 20 + index * 44;
          const y = 118 - (item.tickets / maxTicket) * 88;
          return <circle key={item.mastery} cx={x} cy={y} r="3.5" />;
        })}
      </svg>
      <div className="smart-curve-axis">
        <span>0 分</span>
        <span>掌握度</span>
        <span>100 分</span>
      </div>
      <Text type="secondary" className="block-text">
        当前设置下，掌握度 0 分约 {smartAssessmentTickets(settings, 0).toFixed(1)} 票，50 分约{" "}
        {smartAssessmentTickets(settings, 50).toFixed(1)} 票，100 分固定 1.0 票。
      </Text>
    </div>
  );
}

function PercentSlider({
  value = 0,
  onChange,
  disabled,
}: {
  value?: number;
  onChange?: (value: number) => void;
  disabled?: boolean;
}) {
  const current = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="percent-slider">
      <Slider
        min={0}
        max={100}
        step={5}
        value={current}
        disabled={disabled}
        tooltip={{ formatter: (next) => `${next ?? 0}%` }}
        onChange={(next) => onChange?.(Array.isArray(next) ? next[0] : next)}
      />
      <strong>{current}%</strong>
    </div>
  );
}

function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "????");
}

export function SettingsPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [aiFeatureForm] = Form.useForm();
  const [aiConfigForm] = Form.useForm();
  const platformSettings = useQuery({
    queryKey: ["platform-settings"],
    queryFn: () => api<PlatformSettingsResponse>("/api/admin/platform-settings"),
  });
  const aiConfig = useQuery({
    queryKey: ["ai-configuration", "settings"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });

  useEffect(() => {
    if (platformSettings.data) {
      form.setFieldsValue(platformSettings.data.settings);
    }
  }, [form, platformSettings.data]);

  useEffect(() => {
    if (aiConfig.data) {
      aiConfigForm.setFieldsValue({
        provider: aiConfig.data.provider,
        base_url: aiConfig.data.base_url,
        model: aiConfig.data.model,
        connection_check_interval_minutes: aiConfig.data.connection_check_interval_minutes,
        api_key: "",
        textbook_rag: {
          enabled: aiConfig.data.textbook_rag?.enabled || false,
          elasticsearch_url: aiConfig.data.textbook_rag?.elasticsearch_url || "",
          index_name: aiConfig.data.textbook_rag?.index_name || "canonical-rag-chunks-qwen-v1",
          embedding_dimension: aiConfig.data.textbook_rag?.embedding_dimension || 1024,
          keyword_top_k: aiConfig.data.textbook_rag?.keyword_top_k || 16,
          vector_top_k: aiConfig.data.textbook_rag?.vector_top_k || 24,
          rerank_top_k: aiConfig.data.textbook_rag?.rerank_top_k || 9,
          final_top_k: aiConfig.data.textbook_rag?.final_top_k || 5,
          min_rerank_score: aiConfig.data.textbook_rag?.min_rerank_score || 0,
          timeout_seconds: aiConfig.data.textbook_rag?.timeout_seconds || 8,
          embedding: {
            base_url: aiConfig.data.textbook_rag?.embedding?.base_url || "",
            model: aiConfig.data.textbook_rag?.embedding?.model || "",
            api_key: "",
          },
          rerank: {
            base_url: aiConfig.data.textbook_rag?.rerank?.base_url || "",
            model: aiConfig.data.textbook_rag?.rerank?.model || "",
            api_key: "",
          },
        },
      });
      aiFeatureForm.setFieldsValue({ enabled_features: aiConfig.data.enabled_features });
    }
  }, [aiConfig.data, aiConfigForm, aiFeatureForm]);

  const save = useMutation({
    mutationFn: (values: LearningBehaviorSettings) => putJson<PlatformSettingsResponse>("/api/admin/platform-settings", values),
    onSuccess: () => {
      message.success("设置已保存");
      void queryClient.invalidateQueries({ queryKey: ["platform-settings"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });
  const saveAiFeatures = useMutation({
    mutationFn: (values: { enabled_features?: Partial<AIConfiguration["enabled_features"]> }) => {
      if (!aiConfig.data) {
        throw new Error("AI 接入配置尚未加载");
      }
      const enabledFeatures = {
        ...aiConfig.data.enabled_features,
        ...(values.enabled_features || {}),
      };
      const payload: AIConfigurationUpdate = {
        provider: "openai",
        base_url: aiConfig.data.base_url || "",
        model: aiConfig.data.model || "",
        connection_check_interval_minutes: aiConfig.data.connection_check_interval_minutes || 30,
        enabled_features: enabledFeatures,
      };
      return putJson<AIConfiguration>("/api/admin/ai-configuration", payload);
    },
    onSuccess: () => {
      message.success("学生 AI 能力开关已保存");
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration"] });
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration", "settings"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });
  const saveAiConfig = useMutation({
    mutationFn: (values: AIConfigurationUpdate & { api_key?: string; textbook_rag?: NonNullable<AIConfigurationUpdate["textbook_rag"]> }) => {
      if (!aiConfig.data) {
        throw new Error("AI 接入配置尚未加载");
      }
      const textbookRag = values.textbook_rag || undefined;
      const payload: AIConfigurationUpdate = {
        provider: "openai",
        base_url: values.base_url || "",
        model: values.model || "",
        connection_check_interval_minutes: values.connection_check_interval_minutes || 30,
        enabled_features: aiConfig.data.enabled_features,
        chat_provider: {
          provider: "openai",
          base_url: values.base_url || "",
          model: values.model || "",
        },
      };
      const newSecret = String(values.api_key || "").trim();
      if (newSecret) {
        payload.api_key = newSecret;
        payload.chat_provider = { ...payload.chat_provider!, api_key: newSecret };
      }
      if (textbookRag) {
        const embeddingApiKey = String(textbookRag.embedding?.api_key || "").trim();
        const rerankApiKey = String(textbookRag.rerank?.api_key || "").trim();
        payload.textbook_rag = {
          enabled: Boolean(textbookRag.enabled),
          elasticsearch_url: textbookRag.elasticsearch_url || "",
          index_name: textbookRag.index_name || "canonical-rag-chunks-qwen-v1",
          embedding_dimension: Number(textbookRag.embedding_dimension || 1024),
          keyword_top_k: Number(textbookRag.keyword_top_k || 16),
          vector_top_k: Number(textbookRag.vector_top_k || 24),
          rerank_top_k: Number(textbookRag.rerank_top_k || 9),
          final_top_k: Number(textbookRag.final_top_k || 5),
          min_rerank_score: Number(textbookRag.min_rerank_score || 0),
          timeout_seconds: Number(textbookRag.timeout_seconds || 8),
          embedding: {
            provider: "openai",
            base_url: textbookRag.embedding?.base_url || "",
            model: textbookRag.embedding?.model || "",
            ...(embeddingApiKey ? { api_key: embeddingApiKey } : {}),
          },
          rerank: {
            provider: "openai",
            base_url: textbookRag.rerank?.base_url || "",
            model: textbookRag.rerank?.model || "",
            ...(rerankApiKey ? { api_key: rerankApiKey } : {}),
          },
        };
      }
      return putJson<AIConfiguration>("/api/admin/ai-configuration", payload);
    },
    onSuccess: () => {
      message.success("OpenAI API 接入配置已保存");
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration"] });
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration", "settings"] });
      void queryClient.invalidateQueries({ queryKey: ["learning-assistant-runtime"] });
      aiConfigForm.setFieldsValue({
        api_key: "",
        textbook_rag: { embedding: { api_key: "" }, rerank: { api_key: "" } },
      });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const canEdit = Boolean(platformSettings.data?.can_edit);
  const canEditAiFeatures = Boolean(aiConfig.data?.can_edit);
  const watchedSmartAssessment = Form.useWatch(["assessment", "smart_assessment"], form) as
    | Partial<SmartAssessmentSettings>
    | undefined;
  const smartAssessmentSettings = useMemo(
    () => normalizeSmartAssessmentSettings(watchedSmartAssessment),
    [watchedSmartAssessment],
  );
  const watchedCustomAssessment = Form.useWatch(["assessment", "custom_assessment"], form) as
    | Partial<CustomAssessmentSettings>
    | undefined;
  const customAssessmentSettings = useMemo(
    () => normalizeCustomAssessmentSettings(watchedCustomAssessment),
    [watchedCustomAssessment],
  );

  return (
    <Space orientation="vertical" size={18} className="full">
      <PageTitle title="系统设置" description="控制全体 H5/手机学习端功能、学生 AI 能力，以及 OpenAI API 接入配置。" />
      <QueryState loading={platformSettings.isLoading} error={platformSettings.error}>
        <Form form={form} layout="vertical" onFinish={(values) => save.mutate(values as LearningBehaviorSettings)}>
          <Space orientation="vertical" size={18} className="full">
            {!canEdit ? <Alert type="info" showIcon title="当前账号可查看全局学习端设置，只有管理员可以修改。" /> : null}
            <Card title="测试流程">
              <div className="settings-grid">
                <div className="settings-section">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>课前摸底</Text>
                      <Text type="secondary" className="block-text">
                        控制学生进入章节前是否看到摸底测试。
                      </Text>
                    </div>
                    <Form.Item name={["assessment", "pretest_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                  <Form.Item
                    name={["assessment", "pretest_question_count"]}
                    label="摸底题数"
                    rules={[{ required: true, message: "请输入摸底题数" }]}
                  >
                    <InputNumber min={1} max={50} precision={0} disabled={!canEdit} className="full" />
                  </Form.Item>
                </div>
                <div className="settings-section">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>课后测试</Text>
                      <Text type="secondary" className="block-text">
                        控制章节学习后的巩固测试入口和题量。
                      </Text>
                    </div>
                    <Form.Item name={["assessment", "posttest_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                  <Form.Item
                    name={["assessment", "posttest_question_count"]}
                    label="课后题数"
                    rules={[{ required: true, message: "请输入课后题数" }]}
                  >
                    <InputNumber min={1} max={50} precision={0} disabled={!canEdit} className="full" />
                  </Form.Item>
                </div>
                <div className="settings-section smart-assessment-section">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>智能组卷</Text>
                      <Text type="secondary" className="block-text">
                        学生可直接进入测评；系统按未测实验比例和掌握薄弱倾向抽取实验。
                      </Text>
                    </div>
                    <Form.Item name={["assessment", "smart_assessment", "enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                  <div className="settings-grid smart-settings-grid">
                    <Form.Item
                      name={["assessment", "smart_assessment", "question_count"]}
                      label="测评题数"
                      rules={[{ required: true, message: "请输入智能测评题数" }]}
                    >
                      <InputNumber min={1} max={50} precision={0} disabled={!canEdit} className="full" />
                    </Form.Item>
                    <Form.Item
                      name={["assessment", "smart_assessment", "max_questions_per_experiment"]}
                      label="每个实验最多题数"
                      rules={[{ required: true, message: "请输入每个实验最多题数" }]}
                    >
                      <InputNumber min={1} max={10} precision={0} disabled={!canEdit} className="full" />
                    </Form.Item>
                  </div>
                  <Form.Item
                    name={["assessment", "smart_assessment", "untested_ratio_percent"]}
                    label="未测实验纳入比例"
                    rules={[{ required: true, message: "请选择未测实验纳入比例" }]}
                  >
                    <PercentSlider disabled={!canEdit} />
                  </Form.Item>
                  <Form.Item
                    name={["assessment", "smart_assessment", "weak_tendency_percent"]}
                    label="薄弱倾向"
                    rules={[{ required: true, message: "请选择薄弱倾向" }]}
                  >
                    <PercentSlider disabled={!canEdit} />
                  </Form.Item>
                  <div className="settings-grid smart-settings-grid">
                    <Form.Item
                      name={["assessment", "smart_assessment", "weak_curve"]}
                      label="薄弱曲线系数"
                      help="数值越大，系统越集中照顾低掌握度实验。"
                      rules={[{ required: true, message: "请输入薄弱曲线系数" }]}
                    >
                      <InputNumber min={0.5} max={4} step={0.1} precision={1} disabled={!canEdit} className="full" />
                    </Form.Item>
                    <Form.Item
                      name={["assessment", "smart_assessment", "weak_max_bonus"]}
                      label="最大权重加成"
                      help="控制 0 分实验相对 100 分实验最多可增加多少抽题票。"
                      rules={[{ required: true, message: "请输入最大权重加成" }]}
                    >
                      <InputNumber min={1} max={20} step={0.5} precision={1} disabled={!canEdit} className="full" />
                    </Form.Item>
                  </div>
                  <SmartAssessmentCurve settings={smartAssessmentSettings} />
                </div>
                <div className="settings-section custom-assessment-section">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>自主测评</Text>
                      <Text type="secondary" className="block-text">
                        学生自行选择实验后组卷，适合课前预习、专项复习和临时练习。
                      </Text>
                    </div>
                    <Form.Item name={["assessment", "custom_assessment", "enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                  <div className="settings-grid smart-settings-grid">
                    <Form.Item
                      name={["assessment", "custom_assessment", "default_question_count"]}
                      label="默认题数"
                      rules={[{ required: true, message: "请选择默认题数" }]}
                    >
                      <Select disabled={!canEdit} options={questionCountOptions} />
                    </Form.Item>
                    <Form.Item
                      name={["assessment", "custom_assessment", "max_question_count"]}
                      label="学生可选题量上限"
                      rules={[{ required: true, message: "请选择题量上限" }]}
                    >
                      <Select disabled={!canEdit} options={questionCountOptions} />
                    </Form.Item>
                    <Form.Item
                      name={["assessment", "custom_assessment", "max_questions_per_experiment"]}
                      label="每个实验最多题数"
                      rules={[{ required: true, message: "请输入每个实验最多题数" }]}
                    >
                      <InputNumber min={1} max={10} precision={0} disabled={!canEdit} className="full" />
                    </Form.Item>
                  </div>
                  <Text type="secondary" className="block-text custom-assessment-note">
                    学生端会显示不超过 {customAssessmentSettings.max_question_count} 题的选项；默认进入时选中{" "}
                    {customAssessmentSettings.default_question_count} 题。
                  </Text>
                </div>
              </div>
            </Card>
            <Card title="学习端功能">
              <div className="settings-grid">
                <div className="settings-section compact">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>AI 学习助手入口</Text>
                      <Text type="secondary" className="block-text">
                        控制学生端是否显示课程问答入口；模型调用能力在下方学生 AI 能力中维护。
                      </Text>
                    </div>
                    <Form.Item name={["learning_features", "ai_assistant_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                </div>
                <div className="settings-section compact">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>反馈入口</Text>
                      <Text type="secondary" className="block-text">
                        控制学生是否能提交课程或系统反馈。
                      </Text>
                    </div>
                    <Form.Item name={["learning_features", "feedback_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                </div>
                <div className="settings-section compact">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>教师审核/调试入口</Text>
                      <Text type="secondary" className="block-text">
                        控制学生端是否显示审核预览和调试类入口。
                      </Text>
                    </div>
                    <Form.Item name={["learning_features", "student_review_preview_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                </div>
              </div>
            </Card>
            <Button type="primary" htmlType="submit" loading={save.isPending} disabled={!canEdit}>
              保存设置
            </Button>
          </Space>
          </Form>
      </QueryState>
      <QueryState loading={aiConfig.isLoading} error={aiConfig.error}>
        <Form
          form={aiConfigForm}
          layout="vertical"
          onFinish={(values) =>
            saveAiConfig.mutate(
              values as AIConfigurationUpdate & {
                api_key?: string;
                textbook_rag?: NonNullable<AIConfigurationUpdate["textbook_rag"]>;
              },
            )
          }
        >
          <Card title="OpenAI API 接入" className="settings-ai-config-card">
            {!canEditAiFeatures ? <Alert type="info" showIcon title="当前账号可查看 OpenAI API 配置，只有管理员可以修改。" className="section-alert" /> : null}
            <Text type="secondary" className="block-text ai-card-description">
              配置模型、Base URL、API Key 和自动检测间隔；AI接入页只展示运行状态监控。
            </Text>
            <div className="ai-provider-fixed compact">
              <div>
                <Text type="secondary">供应商</Text>
                <Text strong className="block-text">
                  OpenAI API
                </Text>
              </div>
              <div>
                <Text type="secondary">说明</Text>
                <Text type="secondary" className="block-text">
                  使用 OpenAI API 格式；代理网关可填写 Base URL。保存模型、Base URL 或密钥后会进入新的自动检测周期。
                </Text>
              </div>
            </div>
            <div className="settings-grid">
              <Form.Item name="model" label="模型名称" rules={[{ required: true, message: "请填写模型名称" }]}>
                <Input disabled={!canEditAiFeatures} placeholder="此处填写模型名称" />
              </Form.Item>
              <Form.Item name="base_url" label="Base URL" rules={[{ required: true, message: "请填写AI调用地址" }]}>
                <Input disabled={!canEditAiFeatures} placeholder="此处填写AI调用地址" />
              </Form.Item>
              <Form.Item
                name="api_key"
                label={`API Key${aiConfig.data?.api_key_configured ? `（已配置 ${aiConfig.data.api_key_fingerprint || ""}）` : ""}`}
                required
                rules={[
                  {
                    validator: (_, value) => {
                      if (aiConfig.data?.api_key_configured || String(value || "").trim()) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error("请填写AI调用API Key"));
                    },
                  },
                ]}
              >
                <Input.Password disabled={!canEditAiFeatures} placeholder="此处填写AI调用API Key" autoComplete="new-password" />
              </Form.Item>
              <Form.Item name="connection_check_interval_minutes" label="自动检测间隔（分钟）">
                <InputNumber min={5} max={1440} precision={0} disabled={!canEditAiFeatures} className="full" />
              </Form.Item>
            </div>
            <div className="settings-section">
              <Flex justify="space-between" align="center" gap={12}>
                <div>
                  <Text strong>教材 RAG 检索</Text>
                  <Text type="secondary" className="block-text">
                    用 Elasticsearch + Qwen Embedding/Rerank 为教师出题工作台提供教材证据。
                  </Text>
                </div>
                <Form.Item name={["textbook_rag", "enabled"]} valuePropName="checked" noStyle>
                  <Switch disabled={!canEditAiFeatures} />
                </Form.Item>
              </Flex>
              <div className="settings-grid">
                <Form.Item name={["textbook_rag", "elasticsearch_url"]} label="Elasticsearch URL">
                  <Input disabled={!canEditAiFeatures} placeholder="http://elasticsearch:9200" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "index_name"]} label="教材 chunk 索引">
                  <Input disabled={!canEditAiFeatures} placeholder="canonical-rag-chunks-qwen-v1" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "embedding", "model"]} label="Embedding 模型">
                  <Input disabled={!canEditAiFeatures} placeholder="Qwen embedding model" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "embedding", "base_url"]} label="Embedding Base URL">
                  <Input disabled={!canEditAiFeatures} placeholder="Embedding API 地址" />
                </Form.Item>
                <Form.Item
                  name={["textbook_rag", "embedding", "api_key"]}
                  label={`Embedding API Key${
                    aiConfig.data?.textbook_rag?.embedding?.api_key_configured
                      ? `（已配置 ${aiConfig.data.textbook_rag.embedding.api_key_fingerprint || ""}）`
                      : ""
                  }`}
                >
                  <Input.Password disabled={!canEditAiFeatures} placeholder="留空则保留已有密钥" autoComplete="new-password" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "embedding_dimension"]} label="向量维度">
                  <InputNumber min={1} precision={0} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "rerank", "model"]} label="Rerank 模型">
                  <Input disabled={!canEditAiFeatures} placeholder="Qwen rerank model" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "rerank", "base_url"]} label="Rerank Base URL">
                  <Input disabled={!canEditAiFeatures} placeholder="Rerank API 地址" />
                </Form.Item>
                <Form.Item
                  name={["textbook_rag", "rerank", "api_key"]}
                  label={`Rerank API Key${
                    aiConfig.data?.textbook_rag?.rerank?.api_key_configured
                      ? `（已配置 ${aiConfig.data.textbook_rag.rerank.api_key_fingerprint || ""}）`
                      : ""
                  }`}
                >
                  <Input.Password disabled={!canEditAiFeatures} placeholder="留空则保留已有密钥" autoComplete="new-password" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "keyword_top_k"]} label="关键词召回 TopK">
                  <InputNumber min={1} max={100} precision={0} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "vector_top_k"]} label="向量召回 TopK">
                  <InputNumber min={1} max={100} precision={0} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "rerank_top_k"]} label="重排 TopK">
                  <InputNumber min={1} max={100} precision={0} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "final_top_k"]} label="最终证据 TopK">
                  <InputNumber min={1} max={30} precision={0} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "min_rerank_score"]} label="最小重排分">
                  <InputNumber step={0.05} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
                <Form.Item name={["textbook_rag", "timeout_seconds"]} label="超时（秒）">
                  <InputNumber min={0.5} max={60} step={0.5} disabled={!canEditAiFeatures} className="full" />
                </Form.Item>
              </div>
            </div>
            <div className="settings-card-actions">
              <Button
                type="primary"
                htmlType="submit"
                loading={saveAiConfig.isPending}
                disabled={!canEditAiFeatures}
              >
                保存 OpenAI API 接入
              </Button>
            </div>
          </Card>
        </Form>
        <Form
          form={aiFeatureForm}
          layout="vertical"
          onFinish={(values) => saveAiFeatures.mutate(values as { enabled_features?: Partial<AIConfiguration["enabled_features"]> })}
        >
          <Card
            title="学生 AI 能力"
            extra={<Tag color="default">运行状态在 AI接入 页监控</Tag>}
            className="settings-ai-feature-card"
          >
            {!canEditAiFeatures ? <Alert type="info" showIcon title="当前账号可查看学生 AI 能力开关，只有管理员可以修改。" className="section-alert" /> : null}
            <Text type="secondary" className="block-text ai-card-description">
              这里控制学生端 Agent 能力范围；OpenAI API 接入配置在上方维护，AI接入页只读展示运行状态监控。
            </Text>
            <div className="settings-grid settings-ai-feature-grid">
              <div className="settings-section compact">
                <Flex justify="space-between" align="center" gap={12}>
                  <div>
                    <Text strong>允许学生 AI 接入 RAG</Text>
                    <Text type="secondary" className="block-text">
                      允许学生侧 Agent 检索课本与平台来源作为回答证据。
                    </Text>
                  </div>
                  <Form.Item name={["enabled_features", "rag_access_enabled"]} valuePropName="checked" noStyle>
                    <Switch disabled={!canEditAiFeatures} />
                  </Form.Item>
                </Flex>
              </div>
              <div className="settings-section compact">
                <Flex justify="space-between" align="center" gap={12}>
                  <div>
                    <Text strong>学生 AI 学习助手能力</Text>
                    <Text type="secondary" className="block-text">
                      控制 Agent 是否可响应学生端课程问答；入口开关关闭时学生仍看不到入口。
                    </Text>
                  </div>
                  <Form.Item name={["enabled_features", "student_ai_assistant"]} valuePropName="checked" noStyle>
                    <Switch disabled={!canEditAiFeatures} />
                  </Form.Item>
                </Flex>
              </div>
              <div className="settings-section compact">
                <Flex justify="space-between" align="center" gap={12}>
                  <div>
                    <Text strong>学生 AI 学情分析</Text>
                    <Text type="secondary" className="block-text">
                      控制学生端学习报告和个性化推荐是否可以调用 AI。
                    </Text>
                  </div>
                  <Form.Item name={["enabled_features", "student_learning_analytics"]} valuePropName="checked" noStyle>
                    <Switch disabled={!canEditAiFeatures} />
                  </Form.Item>
                </Flex>
              </div>
            </div>
            <div className="settings-card-actions">
              <Button
                type="primary"
                htmlType="submit"
                loading={saveAiFeatures.isPending}
                disabled={!canEditAiFeatures}
              >
                保存学生 AI 能力
              </Button>
            </div>
          </Card>
        </Form>
      </QueryState>
    </Space>
  );
}
