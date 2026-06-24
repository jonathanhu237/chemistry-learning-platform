import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App as AntApp,
  Button,
  Card,
  Drawer,
  Flex,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Slider,
  Space,
  Statistic,
  Switch,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Typography,
  Upload,
} from "antd";
import {
  ArrowRightOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  EditOutlined,
  IdcardOutlined,
  KeyOutlined,
  PlusOutlined,
  SettingOutlined,
  TeamOutlined,
} from "@ant-design/icons";

import { getSmartAssessmentPreview } from "../../api/classes";
import {
  getClassAssessmentReportPrompts,
  resetClassAssessmentReportPrompts,
  updateClassAssessmentReportPrompts,
  type AssessmentReportPromptSettings,
  type AssessmentReportPromptSettingsResponse,
} from "../../api/assessmentReports";
import type {
  ClassItem,
  CustomAssessmentSettingsResponse,
  RegistrationSettings,
  RosterImportResult,
  RosterStudent,
  SmartAssessmentClassPreviewResponse,
  SmartAssessmentStrategyResponse,
} from "../../api/classes";
import type { CustomAssessmentSettings, SmartAssessmentSettings } from "../../api/settings";
import { api, patchJson, postJson, putJson } from "../../api/http";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { errorMessage } from "../../lib/errors";
import { statusTag } from "../../lib/status";
import "./classes.css";

const { Text, Title } = Typography;

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

function normalizeSmartAssessment(value: Partial<SmartAssessmentSettings> | undefined): SmartAssessmentSettings {
  const clean = Object.fromEntries(Object.entries(value || {}).filter(([, item]) => item !== undefined)) as Partial<SmartAssessmentSettings>;
  return { ...defaultSmartAssessment, ...clean };
}

function normalizeCustomAssessment(value: Partial<CustomAssessmentSettings> | undefined): CustomAssessmentSettings {
  const clean = Object.fromEntries(Object.entries(value || {}).filter(([, item]) => item !== undefined)) as Partial<CustomAssessmentSettings>;
  const merged = { ...defaultCustomAssessment, ...clean };
  return {
    ...merged,
    default_question_count: Math.min(merged.default_question_count, merged.max_question_count),
  };
}

function smartTickets(settings: SmartAssessmentSettings, mastery: number) {
  const weakness = Math.max(0, Math.min(1, (100 - mastery) / 100));
  return 1 + (settings.weak_tendency_percent / 100) * settings.weak_max_bonus * Math.pow(weakness, settings.weak_curve);
}

function ClassSmartCurve({ settings }: { settings: SmartAssessmentSettings }) {
  const marks = [0, 25, 50, 75, 100];
  const max = Math.max(...marks.map((mastery) => smartTickets(settings, mastery)));
  return (
    <div className="class-smart-curve">
      {marks.map((mastery) => {
        const tickets = smartTickets(settings, mastery);
        return (
          <div key={mastery}>
            <span>{mastery}</span>
            <b style={{ width: `${Math.max(8, (tickets / max) * 100)}%` }} />
            <small>{tickets.toFixed(1)} 票</small>
          </div>
        );
      })}
    </div>
  );
}

const previewWarningLabels: Record<string, string> = {
  no_candidate_points: "题库暂无可用于测评的点位题",
  underfilled_by_candidate_points: "候选点位少于目标题数",
  untested_pool_underfilled: "未测点位不足，正式组卷会回填已测点位",
  measured_pool_empty: "暂无已测点位，正式组卷会优先覆盖未测点位",
  experiment_cap_underfilled: "实验题数上限可能导致题量不足",
};

function ClassSmartDataPreview({
  preview,
  loading,
}: {
  preview?: SmartAssessmentClassPreviewResponse;
  loading?: boolean;
}) {
  if (!preview) {
    return (
      <div className="class-smart-data-preview">
        <Text type="secondary">{loading ? "正在估算当前班级分布..." : "暂无班级预估数据"}</Text>
      </div>
    );
  }
  const topExperiments = preview.experiments.slice(0, 6);
  const maxEstimated = Math.max(1, ...topExperiments.map((item) => item.estimated_question_count));
  const warnings = Object.entries(preview.warnings || {})
    .filter(([, active]) => Boolean(active))
    .map(([key]) => previewWarningLabels[key] || key);
  return (
    <div className="class-smart-data-preview">
      <Flex justify="space-between" align="flex-start" gap={12}>
        <div>
          <Text strong>当前班级数据预估</Text>
          <Text type="secondary" className="block-text">
            估算值用于理解策略，正式试卷仍会按题库可用性和会话抽样生成。
          </Text>
        </div>
        <Tag color={preview.source === "class" ? "green" : "default"}>{preview.has_override ? "本班策略" : "继承策略"}</Tag>
      </Flex>
      <div className="class-smart-preview-stats">
        <Statistic title="班级学生" value={preview.class_student_count} />
        <Statistic title="候选点位" value={preview.candidate_point_count} />
        <Statistic title="未测点位" value={preview.untested_point_count} />
        <Statistic title="未测目标" value={`${preview.untested_target_count}/${preview.target_question_count}`} />
      </div>
      {topExperiments.length ? (
        <div className="class-smart-preview-bars">
          {topExperiments.map((item) => (
            <div key={item.id} className="class-smart-preview-row">
              <span>{item.title}</span>
              <b style={{ width: `${Math.max(6, (item.estimated_question_count / maxEstimated) * 100)}%` }} />
              <small>
                约 {item.estimated_question_count.toFixed(1)} 题 · 未测 {item.untested_point_count} · 已测 {item.measured_point_count}
              </small>
            </div>
          ))}
        </div>
      ) : null}
      {warnings.length ? (
        <div className="class-smart-preview-warnings">
          {warnings.map((item) => (
            <Tag key={item} color="gold">
              {item}
            </Tag>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function PercentSlider({
  value = 0,
  onChange,
}: {
  value?: number;
  onChange?: (value: number) => void;
}) {
  const current = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="percent-slider">
      <Slider
        min={0}
        max={100}
        step={5}
        value={current}
        tooltip={{ formatter: (next) => `${next ?? 0}%` }}
        onChange={(next) => onChange?.(Array.isArray(next) ? next[0] : next)}
      />
      <strong>{current}%</strong>
    </div>
  );
}

export function ClassesPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importingRoster, setImportingRoster] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState<string>();
  const [rosterFile, setRosterFile] = useState<File | null>(null);
  const [importMode, setImportMode] = useState<"upsert" | "overwrite">("upsert");
  const [rosterView, setRosterView] = useState<"current" | "disabled">("current");
  const [studentSearch, setStudentSearch] = useState("");
  const [studentOpen, setStudentOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<RosterStudent | null>(null);
  const [classForm] = Form.useForm();
  const [classSettingsForm] = Form.useForm();
  const [registrationForm] = Form.useForm();
  const [smartAssessmentForm] = Form.useForm();
  const [customAssessmentForm] = Form.useForm();
  const [reportPromptForm] = Form.useForm();
  const [studentForm] = Form.useForm();
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const selectedClass = (classes.data || []).find((item) => item.id === selectedClassId) || null;
  const roster = useQuery({
    queryKey: ["class-roster", selectedClassId],
    queryFn: () => api<RosterStudent[]>(`/api/admin/classes/${selectedClassId}/students`),
    enabled: Boolean(selectedClassId),
  });
  const registration = useQuery({
    queryKey: ["class-registration-settings", selectedClassId],
    queryFn: () => api<RegistrationSettings>(`/api/admin/classes/${selectedClassId}/registration-settings`),
    enabled: Boolean(selectedClassId),
  });
  const smartAssessment = useQuery({
    queryKey: ["class-smart-assessment-strategy", selectedClassId],
    queryFn: () => api<SmartAssessmentStrategyResponse>(`/api/admin/classes/${selectedClassId}/smart-assessment-strategy`),
    enabled: Boolean(selectedClassId),
  });
  const smartAssessmentPreview = useQuery({
    queryKey: ["class-smart-assessment-preview", selectedClassId],
    queryFn: () => getSmartAssessmentPreview(selectedClassId || ""),
    enabled: Boolean(selectedClassId),
  });
  const customAssessment = useQuery({
    queryKey: ["class-custom-assessment-settings", selectedClassId],
    queryFn: () => api<CustomAssessmentSettingsResponse>(`/api/admin/classes/${selectedClassId}/custom-assessment-settings`),
    enabled: Boolean(selectedClassId),
  });
  const reportPrompts = useQuery({
    queryKey: ["class-assessment-report-prompts", selectedClassId],
    queryFn: () => getClassAssessmentReportPrompts(selectedClassId || ""),
    enabled: Boolean(selectedClassId),
  });
  const defaultPasswordMode =
    Form.useWatch("default_password_mode", registrationForm) ||
    registration.data?.default_password_mode ||
    (registration.data?.has_default_password ? "shared" : "student_id");
  const classStatus = Form.useWatch("status", classSettingsForm) || selectedClass?.status || "active";
  const watchedSmartQuestionCount = Form.useWatch("question_count", smartAssessmentForm);
  const watchedSmartUntestedRatio = Form.useWatch("untested_ratio_percent", smartAssessmentForm);
  const watchedSmartWeakTendency = Form.useWatch("weak_tendency_percent", smartAssessmentForm);
  const watchedSmartMaxPerExperiment = Form.useWatch("max_questions_per_experiment", smartAssessmentForm);
  const watchedSmartEnabled = Form.useWatch("enabled", smartAssessmentForm);
  const watchedCustomDefaultCount = Form.useWatch("default_question_count", customAssessmentForm);
  const watchedCustomMaxCount = Form.useWatch("max_question_count", customAssessmentForm);
  const watchedCustomMaxPerExperiment = Form.useWatch("max_questions_per_experiment", customAssessmentForm);
  const watchedCustomEnabled = Form.useWatch("enabled", customAssessmentForm);
  const smartPreview = normalizeSmartAssessment({
    ...(smartAssessment.data?.strategy || {}),
    enabled: watchedSmartEnabled,
    question_count: watchedSmartQuestionCount,
    untested_ratio_percent: watchedSmartUntestedRatio,
    weak_tendency_percent: watchedSmartWeakTendency,
    max_questions_per_experiment: watchedSmartMaxPerExperiment,
  });
  const customPreview = normalizeCustomAssessment({
    ...(customAssessment.data?.settings || {}),
    enabled: watchedCustomEnabled,
    default_question_count: watchedCustomDefaultCount,
    max_question_count: watchedCustomMaxCount,
    max_questions_per_experiment: watchedCustomMaxPerExperiment,
  });
  const rosterRows = roster.data || [];
  const currentRoster = rosterRows.filter((row) => row.status !== "disabled");
  const disabledRoster = rosterRows.filter((row) => row.status === "disabled");
  const activeCount = currentRoster.filter((row) => row.activated || row.status === "active").length;
  const inactiveCount = currentRoster.length - activeCount;
  const tableRoster = rosterView === "current" ? currentRoster : disabledRoster;
  const normalizedStudentSearch = studentSearch.trim().toLowerCase();
  const filteredTableRoster = normalizedStudentSearch
    ? tableRoster.filter(
        (row) =>
          row.student_id.toLowerCase().includes(normalizedStudentSearch) ||
          row.student_name.toLowerCase().includes(normalizedStudentSearch),
      )
    : tableRoster;
  const initialPasswordLabel = defaultPasswordMode === "shared" ? "统一初始密码" : "使用学号";

  useEffect(() => {
    if (selectedClass) {
      classSettingsForm.setFieldsValue({
        class_name: selectedClass.class_name,
        description: selectedClass.description,
        status: selectedClass.status,
      });
    }
  }, [classSettingsForm, selectedClass]);

  useEffect(() => {
    if (registration.data) {
      registrationForm.setFieldsValue({
        ...registration.data,
        mode: "roster_only",
        default_password_mode:
          registration.data.default_password_mode || (registration.data.has_default_password ? "shared" : "student_id"),
        default_password: "",
      });
    }
  }, [registration.data, registrationForm]);

  useEffect(() => {
    if (smartAssessment.data) {
      smartAssessmentForm.setFieldsValue(smartAssessment.data.strategy);
    }
  }, [smartAssessment.data, smartAssessmentForm]);

  useEffect(() => {
    if (customAssessment.data) {
      customAssessmentForm.setFieldsValue(customAssessment.data.settings);
    }
  }, [customAssessment.data, customAssessmentForm]);

  useEffect(() => {
    if (reportPrompts.data) {
      reportPromptForm.setFieldsValue(reportPrompts.data.settings);
    }
  }, [reportPromptForm, reportPrompts.data]);

  useEffect(() => {
    if (!studentOpen) return;
    if (editingStudent) {
      studentForm.setFieldsValue(editingStudent);
    } else {
      studentForm.setFieldsValue({
        student_id: "",
        student_name: "",
      });
    }
  }, [editingStudent, studentForm, studentOpen]);

  const createClass = useMutation({
    mutationFn: (values: { class_name: string; description?: string }) => postJson<ClassItem>("/api/admin/classes", values),
    onSuccess: (item) => {
      message.success("班级已创建");
      setCreateOpen(false);
      classForm.resetFields();
      setSelectedClassId(item.id);
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateClass = useMutation({
    mutationFn: (values: { class_name?: string; description?: string; status?: string }) =>
      patchJson<ClassItem>(`/api/admin/classes/${selectedClassId}`, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateRegistration = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      const passwordMode = String(values.default_password_mode || "student_id");
      if (!selectedClassId) throw new Error("请先选择班级");
      return putJson<RegistrationSettings>(`/api/admin/classes/${selectedClassId}/registration-settings`, {
        mode: "roster_only",
        default_password_policy: "student_id_name_activation",
        default_password_mode: passwordMode,
        default_password: passwordMode === "shared" ? values.default_password || undefined : undefined,
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["class-registration-settings", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateSmartAssessment = useMutation({
    mutationFn: (values: SmartAssessmentSettings) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return putJson<SmartAssessmentStrategyResponse>(`/api/admin/classes/${selectedClassId}/smart-assessment-strategy`, values);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["class-smart-assessment-strategy", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["class-smart-assessment-preview", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const resetSmartAssessment = useMutation({
    mutationFn: () => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return api<SmartAssessmentStrategyResponse>(`/api/admin/classes/${selectedClassId}/smart-assessment-strategy`, { method: "DELETE" });
    },
    onSuccess: (response) => {
      message.success("已恢复为全局智能组卷策略");
      smartAssessmentForm.setFieldsValue(response.strategy);
      void queryClient.invalidateQueries({ queryKey: ["class-smart-assessment-strategy", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["class-smart-assessment-preview", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateCustomAssessment = useMutation({
    mutationFn: (values: CustomAssessmentSettings) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return putJson<CustomAssessmentSettingsResponse>(`/api/admin/classes/${selectedClassId}/custom-assessment-settings`, values);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["class-custom-assessment-settings", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const resetCustomAssessment = useMutation({
    mutationFn: () => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return api<CustomAssessmentSettingsResponse>(`/api/admin/classes/${selectedClassId}/custom-assessment-settings`, { method: "DELETE" });
    },
    onSuccess: (response) => {
      message.success("已恢复为全局自主测评设置");
      customAssessmentForm.setFieldsValue(response.settings);
      void queryClient.invalidateQueries({ queryKey: ["class-custom-assessment-settings", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateReportPrompts = useMutation({
    mutationFn: (values: AssessmentReportPromptSettings) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return updateClassAssessmentReportPrompts(selectedClassId, values);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["class-assessment-report-prompts", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const resetReportPrompts = useMutation({
    mutationFn: () => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return resetClassAssessmentReportPrompts(selectedClassId);
    },
    onSuccess: (response: AssessmentReportPromptSettingsResponse) => {
      message.success("已恢复继承全局报告 Prompt");
      reportPromptForm.setFieldsValue(response.settings);
      void queryClient.invalidateQueries({ queryKey: ["class-assessment-report-prompts", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveStudent = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      if (editingStudent) {
        return patchJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${editingStudent.student_id}`, values);
      }
      return postJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students`, values);
    },
    onSuccess: () => {
      message.success(editingStudent ? "学生已更新" : "学生已添加");
      setStudentOpen(false);
      setEditingStudent(null);
      studentForm.resetFields();
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const disableStudent = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return api<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${studentId}`, { method: "DELETE" });
    },
    onSuccess: () => {
      message.success("学生已禁用");
      setRosterView("current");
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const resetPassword = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return postJson(`/api/admin/classes/${selectedClassId}/students/${studentId}/reset-password`, { force_change: true });
    },
    onSuccess: () => message.success("已重置，学生下次登录需使用学号初始密码并修改密码"),
    onError: (error) => message.error(errorMessage(error)),
  });

  const restoreStudent = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return patchJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${studentId}`, { status: "pending" });
    },
    onSuccess: () => {
      message.success("学生已恢复到当前名单");
      setRosterView("current");
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveClassConfiguration = async () => {
    try {
      const [classValues, registrationValues, smartValues, customValues, reportPromptValues] = await Promise.all([
        classSettingsForm.validateFields(),
        registrationForm.validateFields(),
        smartAssessmentForm.validateFields(),
        customAssessmentForm.validateFields(),
        reportPromptForm.validateFields(),
      ]);
      await updateClass.mutateAsync(classValues);
      await updateRegistration.mutateAsync(registrationValues);
      await updateSmartAssessment.mutateAsync(normalizeSmartAssessment(smartValues as Partial<SmartAssessmentSettings>));
      await updateCustomAssessment.mutateAsync(normalizeCustomAssessment(customValues as Partial<CustomAssessmentSettings>));
      await updateReportPrompts.mutateAsync(reportPromptValues as AssessmentReportPromptSettings);
      message.success("班级设置已保存");
      setSettingsOpen(false);
    } catch (error) {
      if (error instanceof Error) {
        message.error(errorMessage(error));
      }
    }
  };

  const importRoster = async () => {
    if (!selectedClassId || !rosterFile) {
      message.warning("请先选择名单文件");
      return;
    }
    const body = new FormData();
    body.append("file", rosterFile);
    body.append("mode", importMode);
    setImportingRoster(true);
    try {
      const result = await api<RosterImportResult>(`/api/admin/classes/${selectedClassId}/roster/import`, { method: "POST", body });
      message.success(
        importMode === "overwrite"
          ? `覆盖导入完成：${result.valid_rows} 条有效，禁用 ${result.disabled_missing} 条缺失名单`
          : `导入完成：${result.valid_rows} 条有效`,
      );
      setRosterFile(null);
      setImportOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    } catch (error) {
      message.error(errorMessage(error));
    } finally {
      setImportingRoster(false);
    }
  };

  const openStudentEditor = (student?: RosterStudent) => {
    setEditingStudent(student || null);
    setStudentOpen(true);
  };

  return (
    <Space orientation="vertical" size={18} className="full">
      <PageTitle title="班级与学生" description="一个班级一张卡片；多个班级可以同时使用，点击卡片后管理班级名单。" />
      <QueryState loading={classes.isLoading} error={classes.error}>
        <div className="class-card-grid">
          {(classes.data || []).map((item) => (
            <Card
              key={item.id}
              hoverable
              className="class-card"
              onClick={() => setSelectedClassId(item.id)}
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter") setSelectedClassId(item.id);
              }}
            >
              <div className="class-card-content">
                <Flex justify="space-between" align="flex-start" gap={12}>
                  <div>
                    <Text className="eyebrow">班级</Text>
                    <Title level={4} className="class-card-title">{item.class_name}</Title>
                  </div>
                  {statusTag(item.status)}
                </Flex>
                <Text type="secondary" className="class-card-description">
                  {item.description || "暂无班级说明"}
                </Text>
                <Flex justify="space-between" align="end" className="class-card-footer">
                  <Statistic title="当前名单" value={item.student_count || 0} prefix={<TeamOutlined />} />
                  <Text className="class-card-action">
                    <ArrowRightOutlined /> 进入管理
                  </Text>
                </Flex>
              </div>
            </Card>
          ))}
          <button type="button" className="class-create-card" onClick={() => setCreateOpen(true)}>
            <PlusOutlined />
            <Text strong>新建班级</Text>
            <Text type="secondary">填写班级名称后即可导入名单</Text>
          </button>
        </div>
      </QueryState>

      <Drawer
        title={selectedClass ? selectedClass.class_name : "班级详情"}
        open={Boolean(selectedClassId)}
        onClose={() => {
          setSelectedClassId(undefined);
          setRosterFile(null);
          setStudentSearch("");
          setSettingsOpen(false);
          setImportOpen(false);
        }}
        size={980}
      >
        {selectedClass ? (
          <Space orientation="vertical" size={18} className="full">
            <div className="class-detail-hero">
              <div className="class-detail-copy">
                <Text className="eyebrow">班级管理</Text>
                <Title level={3}>{selectedClass.class_name}</Title>
                <Space wrap className="class-hero-meta">
                  {statusTag(selectedClass.status)}
                  <Tag color="blue">初始密码：{initialPasswordLabel}</Tag>
                </Space>
                <Text type="secondary" className="class-detail-description">
                  {selectedClass.description || "暂无班级说明"}
                </Text>
              </div>
              <div className="class-hero-side">
                <div className="class-hero-actions">
                  <Button type="primary" icon={<SettingOutlined />} onClick={() => setSettingsOpen(true)}>
                    编辑班级设置
                  </Button>
                </div>
                <div className="class-hero-stats">
                  <Statistic title="当前名单" value={currentRoster.length} prefix={<IdcardOutlined />} />
                  <Statistic title="已激活" value={activeCount} />
                  <Statistic title="未激活" value={inactiveCount} />
                  <Statistic title="已禁用" value={disabledRoster.length} />
                </div>
              </div>
            </div>

            <div className="drawer-section roster-section">
              <Flex justify="space-between" align="flex-start" gap={16} className="drawer-table-heading roster-heading">
                <div className="roster-heading-copy">
                  <Text strong>学生名单</Text>
                  <Text type="secondary" className="block-text">
                    导入或添加即完成班级登记；未激活学生使用班级初始密码首次登录，完成改密后才算已激活。
                  </Text>
                </div>
                <Space className="roster-heading-actions" size={10}>
                  <Button icon={<CloudUploadOutlined />} onClick={() => setImportOpen(true)}>
                    导入名单
                  </Button>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => openStudentEditor()}>
                    添加学生
                  </Button>
                </Space>
              </Flex>
              <Tabs
                activeKey={rosterView}
                onChange={(key) => setRosterView(key as "current" | "disabled")}
                tabBarExtraContent={
                  <Input.Search
                    allowClear
                    className="roster-search"
                    placeholder="搜索学号或姓名"
                    value={studentSearch}
                    onChange={(event) => setStudentSearch(event.target.value)}
                  />
                }
                items={[
                  { key: "current", label: `当前名单 (${currentRoster.length})` },
                  { key: "disabled", label: `已禁用 (${disabledRoster.length})` },
                ]}
              />
              <QueryState loading={roster.isLoading} error={roster.error} empty={!filteredTableRoster.length}>
                <Table<RosterStudent>
                  rowKey="id"
                  dataSource={filteredTableRoster}
                  pagination={{ pageSize: 10, showSizeChanger: true }}
                  size="middle"
                  columns={[
                    { title: "学号", dataIndex: "student_id", width: 150 },
                    { title: "姓名", dataIndex: "student_name" },
                    {
                      title: "状态",
                      width: 120,
                      render: (_: unknown, row) => {
                        if (row.status === "disabled") return <Tag>已禁用</Tag>;
                        if (row.activated || row.status === "active") return <Tag color="green">已激活</Tag>;
                        return <Tag color="gold">未激活</Tag>;
                      },
                    },
                    {
                      title: "操作",
                      width: rosterView === "current" ? 250 : 150,
                      render: (_: unknown, row) => (
                        <Space>
                          <Button icon={<EditOutlined />} onClick={() => openStudentEditor(row)}>
                            编辑
                          </Button>
                          {rosterView === "current" ? (
                            <>
                              <Tooltip
                                title={
                                  row.activated
                                    ? "重置后学生下次登录需使用学号初始密码并修改密码"
                                    : "未激活学生还没有账号，首次登录使用班级初始密码"
                                }
                              >
                                <Button icon={<KeyOutlined />} disabled={!row.activated} onClick={() => resetPassword.mutate(row.student_id)}>
                                  重置
                                </Button>
                              </Tooltip>
                              <Popconfirm title="确认禁用该学生？" onConfirm={() => disableStudent.mutate(row.student_id)}>
                                <Button danger icon={<DeleteOutlined />}>
                                  禁用
                                </Button>
                              </Popconfirm>
                            </>
                          ) : (
                            <Button onClick={() => restoreStudent.mutate(row.student_id)}>
                              恢复
                            </Button>
                          )}
                        </Space>
                      ),
                    },
                  ]}
                />
              </QueryState>
            </div>

          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="班级设置"
        open={settingsOpen}
        okText="保存设置"
        cancelText="取消"
        width={720}
        confirmLoading={
          updateClass.isPending ||
          updateRegistration.isPending ||
          updateSmartAssessment.isPending ||
          updateCustomAssessment.isPending ||
          updateReportPrompts.isPending
        }
        onCancel={() => setSettingsOpen(false)}
        onOk={() => void saveClassConfiguration()}
      >
        <QueryState
          loading={registration.isLoading || smartAssessment.isLoading || customAssessment.isLoading || reportPrompts.isLoading}
          error={registration.error || smartAssessment.error || customAssessment.error || reportPrompts.error}
        >
          <Space orientation="vertical" size={18} className="full">
            <div className="modal-section">
              <Text strong>班级基本信息</Text>
              <Text type="secondary" className="block-text">
                用于老师后台识别班级，学生端只感知自己所属班级。
              </Text>
              <Form form={classSettingsForm} layout="vertical" className="modal-form">
                <Form.Item name="class_name" label="班级名称" rules={[{ required: true, message: "请输入班级名称" }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="description" label="班级说明" rules={[{ max: 200, message: "班级说明请控制在 200 字以内" }]}>
                  <Input.TextArea rows={3} maxLength={200} showCount className="fixed-textarea" />
                </Form.Item>
                <Form.Item name="status" hidden>
                  <Input />
                </Form.Item>
                <div className="option-group-label">班级状态</div>
                <div className="choice-grid two compact">
                  <button
                    type="button"
                    className={`choice-card ${classStatus === "active" ? "choice-card-active" : ""}`}
                    onClick={() => classSettingsForm.setFieldsValue({ status: "active" })}
                  >
                    <Text strong>使用中</Text>
                    <Text type="secondary">学生可以继续学习和做题。</Text>
                  </button>
                  <button
                    type="button"
                    className={`choice-card ${classStatus === "archived" ? "choice-card-active" : ""}`}
                    onClick={() => classSettingsForm.setFieldsValue({ status: "archived" })}
                  >
                    <Text strong>已归档</Text>
                    <Text type="secondary">保留记录，不再作为当前运营班级。</Text>
                  </button>
                </div>
              </Form>
            </div>

            <div className="modal-section">
              <Text strong>登录规则</Text>
              <Text type="secondary" className="block-text">
                当前名单内未激活学生首次登录时使用这里设置的初始密码；已激活学生可从名单中重置为学号初始密码。
              </Text>
              <Form form={registrationForm} layout="vertical" className="modal-form">
                <Form.Item name="mode" hidden>
                  <Input />
                </Form.Item>
                <Form.Item name="default_password_mode" hidden>
                  <Input />
                </Form.Item>
                <div className="option-group-label">初始密码</div>
                <div className="choice-grid two">
                  <button
                    type="button"
                    className={`choice-card ${defaultPasswordMode === "student_id" ? "choice-card-active" : ""}`}
                    onClick={() => registrationForm.setFieldsValue({ default_password_mode: "student_id", default_password: "" })}
                  >
                    <Text strong>使用学号</Text>
                    <Text type="secondary">初始密码等于学号，适合演示和小班。</Text>
                  </button>
                  <button
                    type="button"
                    className={`choice-card ${defaultPasswordMode === "shared" ? "choice-card-active" : ""}`}
                    onClick={() => registrationForm.setFieldsValue({ default_password_mode: "shared" })}
                  >
                    <Text strong>统一初始密码</Text>
                    <Text type="secondary">老师设置一个统一密码，学生首次登录后修改。</Text>
                  </button>
                </div>
                {defaultPasswordMode === "shared" ? (
                  <Form.Item
                    name="default_password"
                    label="统一初始密码"
                    extra={registration.data?.has_default_password ? "留空则继续使用当前统一密码。" : "至少 8 位。"}
                    rules={[
                      {
                        validator: (_, value) => {
                          if (!value && registration.data?.has_default_password) return Promise.resolve();
                          if (!value) return Promise.reject(new Error("请输入统一初始密码"));
                          if (String(value).length < 8) return Promise.reject(new Error("至少 8 位"));
                          return Promise.resolve();
                        },
                      },
                    ]}
                  >
                    <Input.Password placeholder="输入新的统一初始密码" />
                  </Form.Item>
                ) : (
                  <Form.Item label="当前初始密码" extra="初始密码等于学生学号，学生首次登录后必须修改。">
                    <Input value="使用学生学号" disabled />
                  </Form.Item>
                )}
              </Form>
            </div>

            <div className="modal-section">
              <Flex justify="space-between" align="flex-start" gap={12}>
                <div>
                  <Text strong>智能组卷策略</Text>
                  <Text type="secondary" className="block-text">
                    默认继承系统设置；保存后本班会使用这里的题量、未测比例和薄弱倾向。
                  </Text>
                </div>
                <Space>
                  <Tag color={smartAssessment.data?.has_override ? "green" : "default"}>
                    {smartAssessment.data?.has_override ? "本班覆盖" : "全局默认"}
                  </Tag>
                  <Button size="small" loading={resetSmartAssessment.isPending} onClick={() => resetSmartAssessment.mutate()}>
                    恢复默认
                  </Button>
                </Space>
              </Flex>
              <Form form={smartAssessmentForm} layout="vertical" className="modal-form">
                <Flex justify="space-between" align="center" gap={12} className="class-smart-switch">
                  <div>
                    <Text strong>允许学生智能测评</Text>
                    <Text type="secondary" className="block-text">
                      关闭后本班学生无法从测评中心开始智能组卷。
                    </Text>
                  </div>
                  <Form.Item name="enabled" valuePropName="checked" noStyle>
                    <Switch />
                  </Form.Item>
                </Flex>
                <div className="settings-grid class-smart-grid">
                  <Form.Item name="question_count" label="测评题数" rules={[{ required: true, message: "请输入测评题数" }]}>
                    <InputNumber min={1} max={50} precision={0} className="full" />
                  </Form.Item>
                  <Form.Item
                    name="max_questions_per_experiment"
                    label="每个实验最多题数"
                    rules={[{ required: true, message: "请输入每个实验最多题数" }]}
                  >
                    <InputNumber min={1} max={10} precision={0} className="full" />
                  </Form.Item>
                </div>
                <Form.Item name="untested_ratio_percent" label="未测点位纳入比例">
                  <PercentSlider />
                </Form.Item>
                <Form.Item name="weak_tendency_percent" label="薄弱倾向">
                  <PercentSlider />
                </Form.Item>
                <div className="settings-grid class-smart-grid">
                  <Form.Item
                    name="weak_curve"
                    label="薄弱曲线系数"
                    help="数值越大，系统越集中照顾低掌握度点位。"
                    rules={[{ required: true, message: "请输入薄弱曲线系数" }]}
                  >
                    <InputNumber min={0.5} max={4} step={0.1} precision={1} className="full" />
                  </Form.Item>
                  <Form.Item
                    name="weak_max_bonus"
                    label="最大权重加成"
                    help="控制 0 分点位相对 100 分点位最多可增加多少抽题票。"
                    rules={[{ required: true, message: "请输入最大权重加成" }]}
                  >
                    <InputNumber min={1} max={20} step={0.5} precision={1} className="full" />
                  </Form.Item>
                </div>
                <ClassSmartCurve settings={smartPreview} />
                <ClassSmartDataPreview preview={smartAssessmentPreview.data} loading={smartAssessmentPreview.isLoading} />
              </Form>
            </div>
            <div className="modal-section">
              <Flex justify="space-between" align="flex-start" gap={12}>
                <div>
                  <Text strong>自主测评设置</Text>
                  <Text type="secondary" className="block-text">
                    默认继承系统设置；保存后本班学生可以按这里的题量规则自行选择实验练习。
                  </Text>
                </div>
                <Space>
                  <Tag color={customAssessment.data?.has_override ? "green" : "default"}>
                    {customAssessment.data?.has_override ? "本班覆盖" : "全局默认"}
                  </Tag>
                  <Button size="small" loading={resetCustomAssessment.isPending} onClick={() => resetCustomAssessment.mutate()}>
                    恢复默认
                  </Button>
                </Space>
              </Flex>
              <Form form={customAssessmentForm} layout="vertical" className="modal-form">
                <Flex justify="space-between" align="center" gap={12} className="class-smart-switch">
                  <div>
                    <Text strong>允许学生自主测评</Text>
                    <Text type="secondary" className="block-text">
                      关闭后本班学生无法进入自选实验组卷。
                    </Text>
                  </div>
                  <Form.Item name="enabled" valuePropName="checked" noStyle>
                    <Switch />
                  </Form.Item>
                </Flex>
                <div className="settings-grid class-smart-grid">
                  <Form.Item name="default_question_count" label="默认题数" rules={[{ required: true, message: "请选择默认题数" }]}>
                    <Select options={questionCountOptions} />
                  </Form.Item>
                  <Form.Item name="max_question_count" label="学生可选题量上限" rules={[{ required: true, message: "请选择题量上限" }]}>
                    <Select options={questionCountOptions} />
                  </Form.Item>
                  <Form.Item
                    name="max_questions_per_experiment"
                    label="每个实验最多题数"
                    rules={[{ required: true, message: "请输入每个实验最多题数" }]}
                  >
                    <InputNumber min={1} max={10} precision={0} className="full" />
                  </Form.Item>
                </div>
                <Text type="secondary" className="block-text class-custom-note">
                  学生端默认选中 {customPreview.default_question_count} 题，可选题量最高 {customPreview.max_question_count} 题；每个实验最多抽{" "}
                  {customPreview.max_questions_per_experiment} 题。
                </Text>
              </Form>
            </div>
            <div className="modal-section">
              <Flex justify="space-between" align="flex-start" gap={12}>
                <div>
                  <Text strong>测评报告 Prompt</Text>
                  <Text type="secondary" className="block-text">
                    默认继承系统设置；保存后本班报告生成会优先使用这里的总结和错题讲解 Prompt。
                  </Text>
                </div>
                <Space>
                  <Tag color={reportPrompts.data?.has_override ? "green" : "default"}>
                    {reportPrompts.data?.has_override ? "本班覆盖" : "继承全局"}
                  </Tag>
                  <Button size="small" loading={resetReportPrompts.isPending} onClick={() => resetReportPrompts.mutate()}>
                    恢复默认
                  </Button>
                </Space>
              </Flex>
              <div className="class-report-prompt-vars">
                {(reportPrompts.data?.supported_variables || []).map((item) => (
                  <Tag key={item}>{item}</Tag>
                ))}
              </div>
              <Form form={reportPromptForm} layout="vertical" className="modal-form">
                <Form.Item name="summary_prompt" label="报告总结 Prompt" rules={[{ required: true, message: "请输入报告总结 Prompt" }]}>
                  <Input.TextArea rows={6} maxLength={6000} showCount className="fixed-textarea monospace-textarea" />
                </Form.Item>
                <Form.Item name="mistake_prompt" label="错题讲解 Prompt" rules={[{ required: true, message: "请输入错题讲解 Prompt" }]}>
                  <Input.TextArea rows={6} maxLength={6000} showCount className="fixed-textarea monospace-textarea" />
                </Form.Item>
              </Form>
            </div>
          </Space>
        </QueryState>
      </Modal>

      <Modal
        title="导入学生名单"
        open={importOpen}
        okText="导入名单"
        cancelText="取消"
        width={640}
        confirmLoading={importingRoster}
        okButtonProps={{ disabled: !rosterFile }}
        onCancel={() => {
          setImportOpen(false);
          setRosterFile(null);
        }}
        onOk={() => void importRoster()}
      >
        <Space orientation="vertical" size={16} className="full">
          <Text type="secondary">上传 CSV/XLSX。普通导入适合补充名单，覆盖导入适合用一份新名单替换当前名单。</Text>
          <div className="choice-grid two">
            <button
              type="button"
              className={`choice-card ${importMode === "upsert" ? "choice-card-active" : ""}`}
              onClick={() => setImportMode("upsert")}
            >
              <Text strong>普通导入</Text>
              <Text type="secondary">新增学生，更新已有学生姓名，不影响缺失学生。</Text>
            </button>
            <button
              type="button"
              className={`choice-card ${importMode === "overwrite" ? "choice-card-active" : ""}`}
              onClick={() => setImportMode("overwrite")}
            >
              <Text strong>覆盖导入</Text>
              <Text type="secondary">以本次文件为准，缺失学生会被禁用。</Text>
            </button>
          </div>
          <Upload
            maxCount={1}
            beforeUpload={(file) => {
              setRosterFile(file as File);
              return false;
            }}
            onRemove={() => setRosterFile(null)}
          >
            <Button icon={<CloudUploadOutlined />}>选择 CSV/XLSX</Button>
          </Upload>
        </Space>
      </Modal>

      <Modal
        title="新建班级"
        open={createOpen}
        okText="创建班级"
        cancelText="取消"
        confirmLoading={createClass.isPending}
        onCancel={() => setCreateOpen(false)}
        onOk={() => classForm.submit()}
      >
        <Text type="secondary" className="modal-helper">
          只需要填写班级名称，后续可以在班级卡片里导入学生名单。
        </Text>
        <Form form={classForm} layout="vertical" onFinish={(values) => createClass.mutate(values)}>
          <Form.Item name="class_name" label="班级名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="班级说明" rules={[{ max: 200, message: "班级说明请控制在 200 字以内" }]}>
            <Input.TextArea rows={3} maxLength={200} showCount className="fixed-textarea" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingStudent ? "编辑学生" : "添加学生"}
        open={studentOpen}
        okText={editingStudent ? "保存学生" : "添加学生"}
        cancelText="取消"
        onCancel={() => {
          setStudentOpen(false);
          setEditingStudent(null);
        }}
        onOk={() => studentForm.submit()}
      >
        <Text type="secondary" className="modal-helper">
          添加或导入即完成班级登记；学生首次登录并修改密码后会显示为已激活。
        </Text>
        <Form form={studentForm} layout="vertical" onFinish={(values) => saveStudent.mutate(values)}>
          <Form.Item name="student_id" label="学号" rules={[{ required: true }]}>
            <Input disabled={Boolean(editingStudent?.activated)} />
          </Form.Item>
          <Form.Item name="student_name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
