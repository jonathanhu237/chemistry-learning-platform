import { useEffect } from "react";
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
  Space,
  Switch,
  Tag,
  Typography,
} from "antd";

import { api, putJson } from "../../api";
import type {
  AIConfiguration,
  AIConfigurationUpdate,
  LearningBehaviorSettings,
  PlatformSettingsResponse,
} from "../../api";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import "./settings.css";

const { Text } = Typography;

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
    mutationFn: (values: AIConfigurationUpdate & { api_key?: string }) => {
      if (!aiConfig.data) {
        throw new Error("AI 接入配置尚未加载");
      }
      const payload: AIConfigurationUpdate = {
        provider: "openai",
        base_url: values.base_url || "",
        model: values.model || "",
        connection_check_interval_minutes: values.connection_check_interval_minutes || 30,
        enabled_features: aiConfig.data.enabled_features,
      };
      const newSecret = String(values.api_key || "").trim();
      if (newSecret) {
        payload.api_key = newSecret;
      }
      return putJson<AIConfiguration>("/api/admin/ai-configuration", payload);
    },
    onSuccess: () => {
      message.success("OpenAI API 接入配置已保存");
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration"] });
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration", "settings"] });
      void queryClient.invalidateQueries({ queryKey: ["learning-assistant-runtime"] });
      aiConfigForm.setFieldsValue({ api_key: "" });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const canEdit = Boolean(platformSettings.data?.can_edit);
  const canEditAiFeatures = Boolean(aiConfig.data?.can_edit);

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="系统设置" description="控制全体 H5/手机学习端功能、学生 AI 能力，以及 OpenAI API 接入配置。" />
      <QueryState loading={platformSettings.isLoading} error={platformSettings.error}>
        <Form form={form} layout="vertical" onFinish={(values) => save.mutate(values as LearningBehaviorSettings)}>
          <Space direction="vertical" size={18} className="full">
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
          onFinish={(values) => saveAiConfig.mutate(values as AIConfigurationUpdate & { api_key?: string })}
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
