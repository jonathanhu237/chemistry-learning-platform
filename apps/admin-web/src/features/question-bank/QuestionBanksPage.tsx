import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Checkbox,
  Descriptions,
  Divider,
  Drawer,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DatabaseOutlined,
  EditOutlined,
  ExperimentOutlined,
  EyeOutlined,
  MessageOutlined,
  PlusOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";

import { api, patchJson, postJson, postJsonStream } from "../../api";
import type {
  ApiList,
  Experiment,
  ExperimentVideoPointsResponse,
  LearningAssistantRuntime,
  PointAwareSuggestionResponse,
  Question,
  QuestionBankSummary,
  QuestionDraft,
  QuestionWorkbenchCandidate,
  QuestionWorkbenchSession,
} from "../../api";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { useExperiments } from "../experiments/experimentHooks";
import { experimentVideoPointCount } from "../resources/resourceUtils";
import { errorMessage } from "../../lib/errors";
import { optionDiagnosticRoleLabel, statusTag } from "../../lib/status";
import "./question-bank.css";

const { Text, Title } = Typography;

type QuestionFormValues = {
  experiment_id: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options_text?: string;
  answer_text: string;
  explanation?: string;
  difficulty?: string;
  status?: string;
};

function questionTypeLabel(type?: string) {
  if (type === "single_choice") return "??";
  if (type === "true_false") return "??";
  if (type === "fill_blank") return "??";
  return type || "-";
}

function coverageTagLabel(tag?: string) {
  const labels: Record<string, string> = {
    experiment_purpose: "????",
    true_false: "???",
    single_choice: "???",
    fill_blank: "???",
    evidence_based: "???",
    diagnostic: "???",
  };
  return labels[String(tag || "")] || String(tag || "-").replace(/_/g, " ");
}

function answerText(answer?: Record<string, unknown>) {
  if (!answer) return "-";
  if (Array.isArray(answer.accepted_answers)) return answer.accepted_answers.map(String).join("，");
  if (answer.value !== undefined) {
    if (typeof answer.value === "boolean") return answer.value ? "正确" : "错误";
    return String(answer.value);
  }
  return JSON.stringify(answer);
}

function sourceRefLabel(ref: Record<string, unknown>) {
  const file = String(ref.source_file || "资料片段");
  const page = ref.page_number ? ` p.${ref.page_number}` : "";
  const section = ref.section_title ? ` · ${ref.section_title}` : "";
  return `${file}${page}${section}`;
}

function questionPoints(question: Question) {
  const points = question.metadata?.primary_points || [];
  if (points.length) {
    return points
      .map((point) => ({
        point_key: String(point.point_key || "").trim(),
        point_title: String(point.point_title || point.point_key || "").trim(),
      }))
      .filter((point) => point.point_key || point.point_title);
  }
  return (question.metadata?.primary_point_keys || [])
    .map((key) => ({ point_key: String(key), point_title: String(key) }))
    .filter((point) => point.point_key);
}

function questionPointTitles(question: Question) {
  return questionPoints(question).map((point) => point.point_title || point.point_key).filter(Boolean);
}

function draftPayload(draft: QuestionDraft) {
  return draft.payload || {};
}

function draftStem(draft: QuestionDraft) {
  return String(draftPayload(draft).stem || "");
}

function draftQuestionType(draft: QuestionDraft) {
  return String(draftPayload(draft).question_type || "");
}

function draftQuestionPoints(draft: QuestionDraft) {
  const metadata = draftPayload(draft).metadata || {};
  const points = Array.isArray(metadata.primary_points) ? metadata.primary_points : [];
  if (points.length) {
    return points
      .map((point) => ({
        point_key: String(point?.point_key || "").trim(),
        point_title: String(point?.point_title || point?.point_key || "").trim(),
      }))
      .filter((point) => point.point_key || point.point_title);
  }
  const keys = Array.isArray(metadata.primary_point_keys) ? metadata.primary_point_keys : [];
  return keys.map((key) => ({ point_key: String(key), point_title: String(key) })).filter((point) => point.point_key);
}

function candidatePayload(candidate: QuestionWorkbenchCandidate) {
  return candidate.payload || {};
}

function candidateStem(candidate: QuestionWorkbenchCandidate) {
  return String(candidatePayload(candidate).stem || "");
}

function candidateQuestionType(candidate: QuestionWorkbenchCandidate) {
  return String(candidatePayload(candidate).question_type || "");
}

function candidateQuestionPoints(candidate: QuestionWorkbenchCandidate) {
  const metadata = candidatePayload(candidate).metadata || {};
  const points = Array.isArray(metadata.primary_points) ? metadata.primary_points : [];
  if (points.length) {
    return points
      .map((point) => ({
        point_key: String(point?.point_key || "").trim(),
        point_title: String(point?.point_title || point?.point_key || "").trim(),
      }))
      .filter((point) => point.point_key || point.point_title);
  }
  const keys = Array.isArray(metadata.primary_point_keys) ? metadata.primary_point_keys : [];
  return keys.map((key) => ({ point_key: String(key), point_title: String(key) })).filter((point) => point.point_key);
}

function candidateValidationErrors(candidate: QuestionWorkbenchCandidate) {
  return candidate.validation_errors?.length
    ? candidate.validation_errors
    : candidate.draft_validation_errors?.length
      ? candidate.draft_validation_errors
      : [];
}

function questionHasAnyPoint(question: Question, pointKeys: string[]) {
  if (!pointKeys.length) return true;
  const selected = new Set(pointKeys);
  return questionPoints(question).some((point) => selected.has(point.point_key));
}

function evidenceStatusTag(question: Question) {
  if (question.metadata?.source_audit?.evidence_sufficient) return <Tag color="green">证据已核对</Tag>;
  if (question.source_refs?.length) return <Tag color="gold">有来源</Tag>;
  return <Tag>待核对</Tag>;
}

function evidenceStatusText(question: Question) {
  if (question.metadata?.source_audit?.evidence_sufficient) return "证据已核对";
  if (question.source_refs?.length) return "有来源";
  return "待核对";
}

function reviewDecisionText(decision?: string) {
  if (decision === "keep") return "审查保留";
  if (decision === "rewrite") return "建议改写";
  if (decision === "reject") return "已拒绝";
  return "未审查";
}

function questionBankStatusTag(status?: string) {
  if (status === "published") return <Tag color="green">启用</Tag>;
  if (status === "disabled") return <Tag>未启用</Tag>;
  return statusTag(status);
}

function questionBankStatusText(status?: string) {
  if (status === "published") return "启用";
  if (status === "disabled") return "未启用";
  return status || "-";
}

type QuestionWorkbenchGateState = {
  healthy: boolean;
  label: string;
  message: string;
  tagColor: string;
  alertType: "success" | "info" | "warning" | "error";
  bgeStatus: string;
  route: string;
  tone: "ready" | "checking" | "blocked";
};

function questionWorkbenchGateFromRuntime(runtime?: LearningAssistantRuntime): QuestionWorkbenchGateState {
  const ragRuntime = runtime?.rag_runtime;
  const bgeStatus = runtime?.bge_metrics?.ok
    ? "healthy"
    : runtime?.bge_status || (runtime?.bge_error ? "unreachable" : ragRuntime?.bge_service_required ? "checking" : "not_required");
  const route = ragRuntime?.hybrid_bge_enabled
    ? "来源检索正常"
    : ragRuntime?.rag_enabled
      ? "基础来源检索"
      : "来源检索关闭";

  if (!runtime || !ragRuntime) {
    return {
      healthy: false,
      label: "正在检查",
      message: "正在确认来源检索状态，稍等一下再使用 AI 建议。",
      tagColor: "#356f9c",
      alertType: "info",
      bgeStatus: "checking",
      route,
      tone: "checking",
    };
  }
  if (!ragRuntime.rag_enabled) {
    return {
      healthy: false,
      label: "AI 暂不可用",
      message: "来源检索还没开启，暂时不能让 AI 出题或修题。",
      tagColor: "#b42318",
      alertType: "error",
      bgeStatus,
      route,
      tone: "blocked",
    };
  }
  if (!ragRuntime.hybrid_bge_enabled) {
    return {
      healthy: false,
      label: "AI 暂不可用",
      message: "来源检索还没准备好，暂时不能使用 AI 建议。",
      tagColor: "#b42318",
      alertType: "error",
      bgeStatus,
      route,
      tone: "blocked",
    };
  }
  if (!ragRuntime.query_generation_enabled) {
    return {
      healthy: false,
      label: "AI 暂不可用",
      message: "来源检索的扩展查询未开启，暂时不能使用 AI 建议。",
      tagColor: "#b42318",
      alertType: "error",
      bgeStatus,
      route,
      tone: "blocked",
    };
  }
  if (bgeStatus !== "healthy") {
    const statusText: Record<string, string> = {
      checking: "正在检查来源检索服务",
      degraded: "来源检索服务异常",
      unreachable: "来源检索服务连接不上",
      not_configured: "来源检索服务未配置",
    };
    return {
      healthy: false,
      label: bgeStatus === "checking" ? "正在检查" : "AI 暂不可用",
      message: `${statusText[bgeStatus] || "来源检索还没准备好"}，稍后再使用 AI 建议。`,
      tagColor: bgeStatus === "checking" ? "#356f9c" : "#b42318",
      alertType: bgeStatus === "checking" ? "info" : "error",
      bgeStatus,
      route,
      tone: bgeStatus === "checking" ? "checking" : "blocked",
    };
  }
  return {
    healthy: true,
    label: "AI 建议可用",
    message: "会先读取当前实验和点位的来源片段，再生成出题/修题建议。",
    tagColor: "#005826",
    alertType: "success",
    bgeStatus,
    route,
    tone: "ready",
  };
}

export function QuestionBanksPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [experimentId, setExperimentId] = useState<string>();
  const [questionType, setQuestionType] = useState<string>();
  const [pointKeys, setPointKeys] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("published");
  const [search, setSearch] = useState("");
  const [workbenchOpen, setWorkbenchOpen] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [assistantIntent, setAssistantIntent] = useState<"add_questions" | "repair_question">("add_questions");
  const [assistantQuestion, setAssistantQuestion] = useState<Question | null>(null);
  const [assistantPointKey, setAssistantPointKey] = useState<string>();
  const [assistantPointKeys, setAssistantPointKeys] = useState<string[]>([]);
  const [aiWorkbenchOpen, setAiWorkbenchOpen] = useState(false);
  const [aiWorkbenchSessionId, setAiWorkbenchSessionId] = useState<string>();
  const [workbenchPrompt, setWorkbenchPrompt] = useState("");
  const [workbenchQuestionTypes, setWorkbenchQuestionTypes] = useState<Question["question_type"][]>(["single_choice", "true_false"]);
  const [workbenchCount, setWorkbenchCount] = useState(3);
  const [workbenchStreaming, setWorkbenchStreaming] = useState(false);
  const [workbenchStreamStatus, setWorkbenchStreamStatus] = useState("");

  const banks = useQuery({
    queryKey: ["question-banks"],
    queryFn: () => api<ApiList<QuestionBankSummary>>("/api/admin/question-banks"),
  });

  const bankExperiments = banks.data?.items || [];

  useEffect(() => {
    if (!experimentId && bankExperiments.length) {
      const firstWithBank = bankExperiments.find((experiment) =>
        experiment.banks.some((bank) => bank.bank_kind === "default" && Number(bank.published_count || bank.question_count || 0) > 0),
      );
      setExperimentId((firstWithBank || bankExperiments[0]).id);
    }
  }, [bankExperiments, experimentId]);

  const questionParams = new URLSearchParams({ limit: "1000" });
  if (experimentId) questionParams.set("experiment_id", experimentId);
  if (questionType) questionParams.set("question_type", questionType);
  if (statusFilter) questionParams.set("status_filter", statusFilter);
  if (search.trim()) questionParams.set("search", search.trim());

  const questions = useQuery({
    queryKey: ["experiment-bank-questions", questionParams.toString()],
    queryFn: () => api<ApiList<Question>>(`/api/admin/question-banks/questions?${questionParams.toString()}`),
    enabled: Boolean(experimentId),
  });

  const experimentPoints = useQuery({
    queryKey: ["question-bank-video-points", experimentId],
    queryFn: () => api<ExperimentVideoPointsResponse>(`/api/admin/experiments/${experimentId}/video-points`),
    enabled: Boolean(experimentId),
  });

  const drafts = useQuery({
    queryKey: ["question-bank-drafts", experimentId],
    queryFn: () => api<ApiList<QuestionDraft>>(`/api/admin/question-banks/drafts?experiment_id=${experimentId}`),
    enabled: Boolean(experimentId),
  });

  const aiWorkbench = useQuery({
    queryKey: ["question-ai-workbench", aiWorkbenchSessionId],
    queryFn: () => api<QuestionWorkbenchSession>(`/api/admin/question-banks/workbench-sessions/${aiWorkbenchSessionId}`),
    enabled: Boolean(aiWorkbenchOpen && aiWorkbenchSessionId),
  });

  const assistantRuntime = useQuery({
    queryKey: ["learning-assistant-runtime", "question-bank-workbench"],
    queryFn: () => api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime"),
    refetchInterval: 10000,
  });

  const selectedExperiment = useMemo(
    () => bankExperiments.find((item) => item.id === experimentId),
    [bankExperiments, experimentId],
  );
  const selectedBank = selectedExperiment?.banks.find((bank) => bank.bank_kind === "default") || selectedExperiment?.banks[0];

  const totals = useMemo(
    () =>
      bankExperiments.reduce(
        (acc, experiment) => {
          const bank = experiment.banks.find((item) => item.bank_kind === "default") || experiment.banks[0];
          return {
            total: acc.total + Number(bank?.question_count || 0),
            published: acc.published + Number(bank?.published_count || 0),
            choice: acc.choice + Number(bank?.choice_count || 0),
            trueFalse: acc.trueFalse + Number(bank?.true_false_count || 0),
            fillBlank: acc.fillBlank + Number(bank?.fill_blank_count || 0),
          };
        },
        { total: 0, published: 0, choice: 0, trueFalse: 0, fillBlank: 0 },
      ),
    [bankExperiments],
  );

  const pointOptions = useMemo(() => {
    const byKey = new Map<string, string>();
    for (const point of experimentPoints.data?.points || []) {
      if (point.point_key && point.source !== "legacy") byKey.set(point.point_key, point.point_title || point.point_key);
    }
    for (const question of questions.data?.items || []) {
      for (const point of questionPoints(question)) {
        const key = point.point_key || point.point_title;
        if (key && !byKey.has(key)) byKey.set(key, point.point_title || key);
      }
    }
    return [...byKey.entries()].map(([value, label]) => ({ value, label }));
  }, [experimentPoints.data?.points, questions.data?.items]);

  const visibleQuestions = useMemo(
    () => (questions.data?.items || []).filter((question) => questionHasAnyPoint(question, pointKeys)),
    [pointKeys, questions.data?.items],
  );

  const workbenchCandidates = aiWorkbench.data?.candidates || [];
  const workbenchTurns = aiWorkbench.data?.turns || [];
  const workbenchContext = aiWorkbench.data?.context_snapshot || {};
  const workbenchOriginalQuestion = aiWorkbench.data?.original_question_snapshot || assistantQuestion || null;
  const questionWorkbenchGate = questionWorkbenchGateFromRuntime(assistantRuntime.data);
  const workbenchRagGate = workbenchContext.rag_gate;
  const workbenchGateLabel = workbenchRagGate?.healthy === false
    ? String(workbenchRagGate.message || questionWorkbenchGate.message)
    : questionWorkbenchGate.message;
  const workbenchTargetPoints = (workbenchContext.target_points?.length
    ? workbenchContext.target_points
    : workbenchContext.selected_point
      ? [workbenchContext.selected_point]
      : assistantPointKeys.map((key) => ({ point_key: key, point_title: pointOptions.find((option) => option.value === key)?.label || key }))) || [];
  const workbenchEvidencePackage = workbenchContext.evidence_package;
  const workbenchStatusTone = workbenchRagGate?.healthy === false ? "blocked" : questionWorkbenchGate.tone;
  const workbenchEvidenceSourceCount = workbenchEvidencePackage?.source_count ?? (workbenchContext.source_refs || []).length;
  const workbenchEvidenceTitle = workbenchRagGate?.healthy === false
    ? "本轮没有生成"
    : questionWorkbenchGate.healthy
      ? "证据已就绪"
      : questionWorkbenchGate.label;
  const workbenchEvidenceMessage = workbenchRagGate?.healthy === false
    ? workbenchGateLabel
    : questionWorkbenchGate.healthy
      ? "已读取当前实验和点位的来源片段，可以继续用提示细化 AI 建议。"
      : workbenchGateLabel;
  const createTargetPointKeys = pointKeys.filter(Boolean);
  const createTargetPointLabel = createTargetPointKeys.length
    ? `围绕 ${createTargetPointKeys.length} 个点位出题`
    : "未选点位时，将从本实验默认点位开始";

  const openQuestionWorkbench = (question: Question) => {
    setSelectedQuestion(question);
    setWorkbenchOpen(true);
  };

  const closeWorkbench = () => {
    setWorkbenchOpen(false);
    setSelectedQuestion(null);
  };

  const openAddSuggestion = () => {
    if (!questionWorkbenchGate.healthy) {
      message.warning(questionWorkbenchGate.message);
      return;
    }
    const primaryPointKey = pointKeys[0];
    const targetPointKeys = pointKeys.filter(Boolean);
    setAssistantIntent("add_questions");
    setAssistantQuestion(null);
    setAssistantPointKey(primaryPointKey);
    setAssistantPointKeys(targetPointKeys);
    setWorkbenchPrompt(selectedExperiment ? `为《${selectedExperiment.code} ${selectedExperiment.title}》补充点位诊断题。` : "补充点位诊断题。");
    setWorkbenchQuestionTypes(["single_choice", "true_false"]);
    setWorkbenchCount(3);
    if (experimentId) {
      startWorkbench.mutate({
        mode: "create",
        experiment_id: experimentId,
        point_key: primaryPointKey || null,
        point_keys: targetPointKeys,
      });
    }
  };

  const openRepairSuggestion = (question: Question) => {
    if (!questionWorkbenchGate.healthy) {
      message.warning(questionWorkbenchGate.message);
      return;
    }
    const questionPointKeys = questionPoints(question).map((point) => point.point_key).filter(Boolean) as string[];
    setAssistantIntent("repair_question");
    setAssistantQuestion(question);
    setWorkbenchOpen(false);
    setAssistantPointKey(questionPoints(question)[0]?.point_key);
    setAssistantPointKeys(questionPointKeys);
    setWorkbenchPrompt("请基于当前实验点位、来源证据和选项诊断链接，给出一版更清晰、更可诊断的修正题。");
    setWorkbenchQuestionTypes([question.question_type]);
    setWorkbenchCount(1);
    startWorkbench.mutate({
      mode: "repair",
      experiment_id: question.experiment_id,
      question_id: question.id,
      point_key: questionPoints(question)[0]?.point_key || null,
      point_keys: questionPointKeys,
    });
  };

  const refreshQuestionBank = () => {
    void queryClient.invalidateQueries({ queryKey: ["question-banks"] });
    void queryClient.invalidateQueries({ queryKey: ["question-bank-drafts", experimentId] });
    void queryClient.invalidateQueries({ queryKey: ["experiment-bank-questions"] });
  };

  const startWorkbench = useMutation({
    mutationFn: (payload: {
      mode: "repair" | "create";
      experiment_id: string;
      question_id?: string | null;
      point_key?: string | null;
      point_keys?: string[];
    }) => postJson<QuestionWorkbenchSession>("/api/admin/question-banks/workbench-sessions", payload),
    onSuccess: (result) => {
      setAiWorkbenchSessionId(result.id);
      setAiWorkbenchOpen(true);
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", result.id] });
    },
    onError: (error) => message.error(`AI 工作台打开失败：${errorMessage(error)}`),
  });

  const sendWorkbenchMessage = async () => {
    if (!aiWorkbenchSessionId || !workbenchPrompt.trim() || workbenchStreaming) return;
    if (!questionWorkbenchGate.healthy) {
      message.warning(questionWorkbenchGate.message);
      return;
    }
    const prompt = workbenchPrompt.trim();
    setWorkbenchStreaming(true);
    setWorkbenchStreamStatus("已发送提示，等待 AI 开始生成");
    try {
      await postJsonStream<{ message?: string; session?: QuestionWorkbenchSession }>(
        `/api/admin/question-banks/workbench-sessions/${aiWorkbenchSessionId}/messages/stream`,
        {
          prompt,
          question_types: workbenchQuestionTypes,
          count: workbenchCount,
          difficulty: "basic",
        },
        ({ event, data }) => {
          if (event === "status") {
            setWorkbenchStreamStatus(String(data.message || "AI 正在生成候选题"));
          }
          if (event === "final" && data.session) {
            queryClient.setQueryData(["question-ai-workbench", aiWorkbenchSessionId], data.session);
            message.success("AI 候选已更新");
            setWorkbenchPrompt("");
            void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
            refreshQuestionBank();
          }
          if (event === "error") {
            throw new Error(String(data.message || "AI 生成失败"));
          }
        },
      );
    } catch (error) {
      message.error(`AI 生成失败：${errorMessage(error)}`);
    } finally {
      setWorkbenchStreaming(false);
      setWorkbenchStreamStatus("");
    }
  };

  const publishCandidate = useMutation({
    mutationFn: (candidateId: string) => postJson<Question>(`/api/admin/question-banks/workbench-candidates/${candidateId}/publish`, {}),
    onSuccess: () => {
      message.success("候选已发布为生成题");
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      refreshQuestionBank();
    },
    onError: (error) => message.error(`发布失败：${errorMessage(error)}`),
  });

  const rejectCandidate = useMutation({
    mutationFn: (candidateId: string) => postJson<QuestionWorkbenchCandidate>(`/api/admin/question-banks/workbench-candidates/${candidateId}/reject`, {}),
    onSuccess: () => {
      message.success("候选已拒绝");
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      refreshQuestionBank();
    },
    onError: (error) => message.error(`拒绝失败：${errorMessage(error)}`),
  });

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="题库管理"
        description="按正式实验和实验点位查看当前发布题库，核对题目、证据来源和单选诊断链接。"
      />

      <div className="stat-grid question-bank-stat-grid">
        <Card>
          <Statistic title="当前题库" value={totals.total} suffix="题" prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="已发布" value={totals.published} suffix="题" prefix={<CheckCircleOutlined />} />
        </Card>
        <Card>
          <Statistic title="选择题" value={totals.choice} suffix="题" />
        </Card>
        <Card>
          <Statistic title="填空题" value={totals.fillBlank} suffix="题" />
        </Card>
        <Card>
          <Statistic title="判断题" value={totals.trueFalse} suffix="题" />
        </Card>
      </div>

      <div className="question-bank-layout">
        <Card className="question-chapter-panel" title="实验题库" extra={<Tag color="green">{bankExperiments.length} 个实验</Tag>}>
          <Text type="secondary" className="question-card-helper">
            先选实验，再按点位查看题目。
          </Text>
          <QueryState loading={banks.isLoading} error={banks.error} empty={!bankExperiments.length}>
            <Table
              rowKey="id"
              size="small"
              pagination={{ pageSize: 12, showSizeChanger: false }}
              dataSource={bankExperiments}
              rowClassName={(row) => (row.id === experimentId ? "question-chapter-row-active" : "")}
              onRow={(record) => ({
                onClick: () => {
                  setExperimentId(record.id);
                  setQuestionType(undefined);
                  setPointKeys([]);
                  setSearch("");
                  setSelectedQuestion(null);
                  setWorkbenchOpen(false);
                },
              })}
              columns={[
                {
                  title: "实验",
                  render: (_: unknown, row: QuestionBankSummary) => {
                    const bank = row.banks.find((item) => item.bank_kind === "default") || row.banks[0];
                    const published = Number(bank?.published_count || row.published_question_count || 0);
                    return (
                      <Space direction="vertical" size={3} className="question-bank-experiment-cell">
                        <Text strong>
                          {row.code} {row.title}
                        </Text>
                        <Text type="secondary">
                          {experimentVideoPointCount(row)} 个点位 · {published} 题 · 选 {Number(bank?.choice_count || 0)} · 判{" "}
                          {Number(bank?.true_false_count || 0)} · 填 {Number(bank?.fill_blank_count || 0)}
                        </Text>
                      </Space>
                    );
                  },
                },
              ]}
            />
          </QueryState>
        </Card>

        <Card title="当前实验题目" className="question-bank-question-panel">
          <Flex justify="space-between" gap={16} wrap="wrap" className="question-list-heading">
            <div>
              <Title level={3}>
                {selectedExperiment ? `${selectedExperiment.code} ${selectedExperiment.title}` : "请选择实验"}
              </Title>
              <Text type="secondary" className="question-bank-summary-line">
                已发布 {selectedBank?.published_count || 0} 题 · 选择 {selectedBank?.choice_count || 0} · 判断{" "}
                {selectedBank?.true_false_count || 0} · 填空 {selectedBank?.fill_blank_count || 0}
              </Text>
            </div>
            <Space wrap className="question-list-heading-actions">
              <Tooltip title={questionWorkbenchGate.healthy ? createTargetPointLabel : questionWorkbenchGate.message}>
                <Button
                  type="primary"
                  icon={<MessageOutlined />}
                  onClick={openAddSuggestion}
                  disabled={!experimentId || !questionWorkbenchGate.healthy}
                >
                  AI 新增建议
                </Button>
              </Tooltip>
            </Space>
          </Flex>

          <div className={`question-workbench-status question-workbench-status-${questionWorkbenchGate.tone}`} role="status">
            <div className="question-workbench-status-main">
              <span className="question-workbench-status-icon">
                {questionWorkbenchGate.tone === "ready" ? (
                  <CheckCircleOutlined />
                ) : questionWorkbenchGate.tone === "checking" ? (
                  <ReloadOutlined />
                ) : (
                  <CloseCircleOutlined />
                )}
              </span>
              <div className="question-workbench-status-copy">
                <Text strong>{questionWorkbenchGate.label}</Text>
                <Text type="secondary">{questionWorkbenchGate.message}</Text>
              </div>
            </div>
            <div className="question-workbench-status-meta">
              <span>{questionWorkbenchGate.route}</span>
              <span>{createTargetPointLabel}</span>
            </div>
          </div>

          <div className="question-bank-actions">
            <Select
              allowClear
              className="question-bank-type-filter"
              placeholder="题型"
              value={questionType}
              onChange={setQuestionType}
              options={[
                { value: "single_choice", label: "选择" },
                { value: "true_false", label: "判断" },
                { value: "fill_blank", label: "填空" },
              ]}
            />
            <Select
              allowClear
              className="question-bank-point-filter"
              mode="multiple"
              maxTagCount="responsive"
              placeholder="实验点位"
              value={pointKeys}
              onChange={(values) => setPointKeys(values)}
              showSearch
              optionFilterProp="label"
              options={pointOptions}
            />
            <Select
              className="question-bank-status-filter"
              placeholder="状态"
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: "published", label: "已发布" },
                { value: "disabled", label: "已停用" },
                { value: "draft", label: "草稿" },
              ]}
            />
            <Input.Search
              allowClear
              className="question-bank-search"
              placeholder="搜索题干或解析"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onSearch={setSearch}
            />
          </div>

          <QueryState loading={questions.isLoading} error={questions.error} empty={!visibleQuestions.length}>
            <Table
              rowKey="id"
              dataSource={visibleQuestions}
              pagination={{ pageSize: 8 }}
              onRow={(record) => ({ onClick: () => openQuestionWorkbench(record) })}
              columns={[
                { title: "题型", width: 64, dataIndex: "question_type", render: questionTypeLabel },
                { title: "题干", dataIndex: "stem" },
                {
                  title: "主点位",
                  width: 154,
                  render: (_: unknown, row: Question) => {
                    const points = questionPointTitles(row);
                    const primaryPoint = points[0];
                    if (!primaryPoint) return <Text type="secondary">-</Text>;
                    return (
                      <Tooltip
                        title={
                          <div className="question-point-tooltip-list">
                            {points.map((title) => (
                              <span key={title}>{title}</span>
                            ))}
                          </div>
                        }
                      >
                        <span className="question-point-stack">
                          <span className="question-point-pill">{primaryPoint}</span>
                          {points.length > 1 ? <span className="question-point-count">共 {points.length} 个</span> : null}
                        </span>
                      </Tooltip>
                    );
                  },
                },
                {
                  title: "证据",
                  width: 96,
                  render: (_: unknown, row: Question) => (
                    <Space direction="vertical" size={2}>
                      {evidenceStatusTag(row)}
                      <Text type="secondary">{row.source_refs?.length || 0} 条来源</Text>
                    </Space>
                  ),
                },
                { title: "状态", width: 72, dataIndex: "status", render: questionBankStatusTag },
                {
                  title: "操作",
                  width: 56,
                  render: (_: unknown, row: Question) => (
                    <Tooltip title="查看题目详情">
                      <Button
                        type="text"
                        icon={<EyeOutlined />}
                        aria-label="查看题目详情"
                        onClick={(event) => {
                          event.stopPropagation();
                          openQuestionWorkbench(row);
                        }}
                      />
                    </Tooltip>
                  ),
                },
              ]}
            />
          </QueryState>
        </Card>
      </div>

      <Modal
        title="题目详情"
        open={workbenchOpen}
        width={980}
        onCancel={closeWorkbench}
        footer={
          selectedQuestion
            ? [
                <Button
                  key="repair"
                  type="primary"
                  icon={<MessageOutlined />}
                  disabled={!questionWorkbenchGate.healthy}
                  title={questionWorkbenchGate.healthy ? "" : questionWorkbenchGate.message}
                  onClick={() => openRepairSuggestion(selectedQuestion)}
                >
                  AI 修正建议
                </Button>,
                <Button key="close" onClick={closeWorkbench}>
                  关闭
                </Button>,
              ]
            : [
                <Button key="close" onClick={closeWorkbench}>
                  关闭
                </Button>,
              ]
        }
      >
        {selectedQuestion ? (
          <Space direction="vertical" size={16} className="full">
            <div className="modal-section question-detail-card">
              <div>
                <Title level={4}>{selectedQuestion.stem}</Title>
                <div className="question-detail-meta-grid">
                  <span className="question-detail-fact">
                    <span className="question-detail-fact-label">题型</span>
                    <span className="question-detail-fact-value">{questionTypeLabel(selectedQuestion.question_type)}</span>
                  </span>
                  <span className="question-detail-fact">
                    <span className="question-detail-fact-label">状态</span>
                    <span className="question-detail-fact-value">{questionBankStatusText(selectedQuestion.status)}</span>
                  </span>
                  <span className="question-detail-fact">
                    <span className="question-detail-fact-label">证据</span>
                    <span className="question-detail-fact-value">{evidenceStatusText(selectedQuestion)}</span>
                  </span>
                  {selectedQuestion.experiment_code || selectedQuestion.experiment_title ? (
                    <span className="question-detail-fact question-detail-fact-wide">
                      <span className="question-detail-fact-label">所属实验</span>
                      <span className="question-detail-fact-value">
                        {selectedQuestion.experiment_code} {selectedQuestion.experiment_title}
                      </span>
                    </span>
                  ) : null}
                </div>
              </div>

              {selectedQuestion.options?.length ? (
                <div className="question-options question-workbench-options">
                  {selectedQuestion.options.map((option, index) => {
                    const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
                    const text = typeof option === "string" ? option : option.text || "";
                    return (
                      <div key={`${label}-${index}`} className="question-option">
                        <Text strong>{label}</Text>
                        <Text>{text}</Text>
                      </div>
                    );
                  })}
                </div>
              ) : null}

              <Descriptions size="small" column={1} className="question-workbench-descriptions">
                <Descriptions.Item label="确定性答案">{answerText(selectedQuestion.answer)}</Descriptions.Item>
                <Descriptions.Item label="解析">{selectedQuestion.explanation || "暂无解析"}</Descriptions.Item>
              </Descriptions>

              <div className="question-point-section">
                <Flex justify="space-between" align="center" gap={10} wrap="wrap">
                  <Text strong>点位与证据核查</Text>
                  <Text type="secondary">
                    {reviewDecisionText(selectedQuestion.metadata?.review_decision)} · {evidenceStatusText(selectedQuestion)}
                  </Text>
                </Flex>
                <div className="question-evidence-grid">
                  <div className="question-evidence-row">
                    <Text type="secondary">实验点位</Text>
                    <div className="question-evidence-values">
                      {questionPointTitles(selectedQuestion).length ? (
                        questionPointTitles(selectedQuestion).map((title) => (
                          <span key={title} className="question-evidence-pill is-point">
                            {title}
                          </span>
                        ))
                      ) : (
                        <Text type="secondary">未绑定点位</Text>
                      )}
                    </div>
                  </div>
                  {selectedQuestion.metadata?.coverage_tags?.length ? (
                    <div className="question-evidence-row">
                      <Text type="secondary">诊断维度</Text>
                      <div className="question-evidence-values">
                        {selectedQuestion.metadata.coverage_tags.map((tag) => (
                          <span key={tag} className="question-evidence-pill">
                            {coverageTagLabel(tag)}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="question-evidence-row">
                    <Text type="secondary">核心来源片段</Text>
                    <div className="question-evidence-values">
                      {(selectedQuestion.metadata?.source_audit?.canonical_chunk_ids || []).length ? (
                        (selectedQuestion.metadata?.source_audit?.canonical_chunk_ids || []).map((chunkId) => (
                          <code key={chunkId} className="question-evidence-code">
                            {chunkId}
                          </code>
                        ))
                      ) : (
                        <Text type="secondary">暂无记录</Text>
                      )}
                    </div>
                  </div>
                  <div className="question-evidence-row">
                    <Text type="secondary">理论支撑片段</Text>
                    <div className="question-evidence-values">
                      {(selectedQuestion.metadata?.source_audit?.supporting_theory_chunk_ids || []).length ? (
                        (selectedQuestion.metadata?.source_audit?.supporting_theory_chunk_ids || []).map((chunkId) => (
                          <code key={chunkId} className="question-evidence-code">
                            {chunkId}
                          </code>
                        ))
                      ) : (
                        <Text type="secondary">暂无单独理论片段</Text>
                      )}
                    </div>
                  </div>
                  {selectedQuestion.metadata?.source_audit?.reviewer_note ? (
                    <div className="question-evidence-row">
                      <Text type="secondary">审查备注</Text>
                      <Text>{selectedQuestion.metadata.source_audit.reviewer_note}</Text>
                    </div>
                  ) : null}
                </div>
              </div>

              {selectedQuestion.metadata?.option_links?.length ? (
                <div className="question-source-section">
                  <Text strong>选项诊断链接</Text>
                  <Table
                    rowKey={(row) => String(row.label || row.role || Math.random())}
                    size="small"
                    pagination={false}
                    dataSource={selectedQuestion.metadata.option_links}
                    columns={[
                      { title: "选项", dataIndex: "label", width: 70 },
                      { title: "角色", dataIndex: "role", width: 120, render: optionDiagnosticRoleLabel },
                      {
                        title: "点位/说明",
                        render: (_: unknown, row) => row.point_title || row.point_key || row.diagnostic_note || "-",
                      },
                    ]}
                  />
                </div>
              ) : null}

              {selectedQuestion.source_refs?.length ? (
                <div className="question-source-section">
                  <Text strong>来源依据</Text>
                  <div className="question-source-list question-source-list-stacked">
                    {selectedQuestion.source_refs.map((ref, index) => (
                      <div key={`${ref.chunk_id || index}`} className="question-source-item">
                        {sourceRefLabel(ref)}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择题目" />
        )}
      </Modal>

      <Drawer
        title={assistantIntent === "repair_question" ? "AI 修题工作台" : "AI 新增题工作台"}
        open={aiWorkbenchOpen}
        width="min(1280px, 96vw)"
        onClose={() => setAiWorkbenchOpen(false)}
        className="ai-question-workbench-drawer"
        extra={
          <Button
            type="primary"
            icon={<MessageOutlined />}
            loading={workbenchStreaming}
            disabled={!aiWorkbenchSessionId || !workbenchPrompt.trim() || workbenchStreaming || !questionWorkbenchGate.healthy}
            onClick={sendWorkbenchMessage}
          >
            发送提示
          </Button>
        }
      >
        <QueryState loading={aiWorkbench.isLoading || startWorkbench.isPending} error={aiWorkbench.error}>
          <div className="ai-workbench-grid">
            <section className="ai-workbench-panel ai-workbench-context">
              <Flex justify="space-between" align="center" gap={10} wrap="wrap" className="ai-workbench-section-head">
                <div>
                  <Text className="eyebrow">{assistantIntent === "repair_question" ? "原题上下文" : "新增上下文"}</Text>
                  <Title level={4}>
                    {aiWorkbench.data?.experiment_code || selectedExperiment?.code} {aiWorkbench.data?.experiment_title || selectedExperiment?.title}
                  </Title>
                </div>
                <Tag color={assistantIntent === "repair_question" ? "gold" : "blue"}>
                  {assistantIntent === "repair_question" ? "修题会话" : "新增会话"}
                </Tag>
              </Flex>
              <div className={`question-workbench-status question-workbench-status-${workbenchStatusTone}`}>
                <div className="question-workbench-status-main">
                  <span className="question-workbench-status-icon">
                    {workbenchStatusTone === "ready" ? (
                      <CheckCircleOutlined />
                    ) : workbenchStatusTone === "checking" ? (
                      <ReloadOutlined />
                    ) : (
                      <CloseCircleOutlined />
                    )}
                  </span>
                  <div className="question-workbench-status-copy">
                    <Text strong>{workbenchEvidenceTitle}</Text>
                    <Text type="secondary">{workbenchEvidenceMessage}</Text>
                  </div>
                </div>
                <div className="question-workbench-status-meta">
                  <span>来源 {workbenchEvidenceSourceCount} 条</span>
                  {workbenchTargetPoints.length ? <span>{workbenchTargetPoints.length} 个目标点位</span> : null}
                </div>
              </div>

              {assistantIntent === "repair_question" && workbenchOriginalQuestion ? (
                <Space direction="vertical" size={12} className="full">
                  <div className="ai-workbench-original-card">
                    <Text strong>{String(workbenchOriginalQuestion.stem || "")}</Text>
                    <Space wrap className="question-detail-meta">
                      <Tag color="blue">{questionTypeLabel(String(workbenchOriginalQuestion.question_type || ""))}</Tag>
                      {workbenchOriginalQuestion.status ? questionBankStatusTag(String(workbenchOriginalQuestion.status)) : null}
                    </Space>
                    {Array.isArray(workbenchOriginalQuestion.options) && workbenchOriginalQuestion.options.length ? (
                      <div className="question-options">
                        {workbenchOriginalQuestion.options.map((option, index) => {
                          const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
                          const text = typeof option === "string" ? option : option.text || "";
                          return (
                            <div key={`${label}-${index}`} className="question-option">
                              <Text strong>{label}</Text>
                              <Text>{text}</Text>
                            </div>
                          );
                        })}
                      </div>
                    ) : null}
                    <Descriptions size="small" column={1} className="question-workbench-descriptions">
                      <Descriptions.Item label="答案">{answerText(workbenchOriginalQuestion.answer as Record<string, unknown>)}</Descriptions.Item>
                      <Descriptions.Item label="解析">{String(workbenchOriginalQuestion.explanation || "暂无解析")}</Descriptions.Item>
                    </Descriptions>
                  </div>
                </Space>
              ) : (
                <div className="ai-workbench-original-card">
                  <Text strong>当前实验与点位</Text>
                  <Descriptions size="small" column={1} className="question-workbench-descriptions">
                    <Descriptions.Item label="目标点位">
                      {workbenchTargetPoints.length
                        ? workbenchTargetPoints.map((point) => point.point_title || point.point_key).join("、")
                        : assistantPointKey || "全部点位"}
                    </Descriptions.Item>
                    <Descriptions.Item label="已有题量">{workbenchContext.coverage?.question_count ?? "-"}</Descriptions.Item>
                    <Descriptions.Item label="该点位题量">{workbenchContext.coverage?.selected_point_question_count ?? "-"}</Descriptions.Item>
                  </Descriptions>
                </div>
              )}

              <div className="question-point-section">
                <Text strong>点位与证据</Text>
                <Space wrap className="question-point-list">
                  {workbenchTargetPoints.map((point) => (
                    <Tag key={point.point_key || point.point_title} color="cyan">
                      {point.point_title || point.point_key}
                    </Tag>
                  ))}
                  {!workbenchTargetPoints.length && workbenchOriginalQuestion?.metadata
                    ? questionPoints(workbenchOriginalQuestion as Question).map((point) => (
                        <Tag key={point.point_key || point.point_title} color="cyan">
                          {point.point_title || point.point_key}
                        </Tag>
                      ))
                    : null}
                </Space>
                <Space wrap className="question-source-list">
                  {(workbenchContext.source_refs || []).slice(0, 8).map((ref, index) => (
                    <Tag key={`${ref.chunk_id || index}`}>{sourceRefLabel(ref)}</Tag>
                  ))}
                  {!(workbenchContext.source_refs || []).length ? <Tag>暂无来源片段</Tag> : null}
                </Space>
              </div>

              {workbenchOriginalQuestion?.metadata?.option_links?.length ? (
                <div className="question-source-section">
                  <Text strong>原题选项诊断</Text>
                  <Table
                    rowKey={(row) => String(row.label || row.role || row.diagnostic_note || Math.random())}
                    size="small"
                    pagination={false}
                    dataSource={workbenchOriginalQuestion.metadata.option_links}
                    columns={[
                      { title: "选项", dataIndex: "label", width: 64 },
                      { title: "角色", dataIndex: "role", width: 110, render: optionDiagnosticRoleLabel },
                      { title: "说明", render: (_: unknown, row) => row.point_title || row.point_key || row.diagnostic_note || "-" },
                    ]}
                  />
                </div>
              ) : null}
            </section>

            <section className="ai-workbench-panel ai-workbench-chat">
              <Flex justify="space-between" align="center" gap={10} className="ai-workbench-section-head">
                <div>
                  <Text className="eyebrow">多轮提示</Text>
                  <Title level={4}>会话记录</Title>
                </div>
                <Space size={6} wrap>
                  {workbenchStreaming && workbenchStreamStatus ? <Tag color="processing">{workbenchStreamStatus}</Tag> : null}
                  <Tag>{workbenchTurns.length} 轮</Tag>
                </Space>
              </Flex>
              <div className="ai-workbench-chat-timeline">
                {workbenchTurns.length ? (
                  workbenchTurns.map((turn) => (
                    <div key={turn.id} className={`ai-chat-turn ai-chat-turn-${turn.role}`}>
                      <Text strong>{turn.role === "user" ? "老师" : "AI"}</Text>
                      <Text className="block-text">{turn.content}</Text>
                      {turn.error_state ? <Alert type="error" showIcon message="本轮生成失败" description={String(turn.error_state.message || "")} /> : null}
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有开始对话" />
                )}
                {workbenchStreaming ? (
                  <div className="ai-chat-turn ai-chat-turn-assistant">
                    <Flex align="center" gap={8}>
                      <Text strong>AI</Text>
                      <Spin size="small" />
                    </Flex>
                    <Text className="block-text">{workbenchStreamStatus || "正在生成候选题..."}</Text>
                  </div>
                ) : null}
              </div>
              <div className="ai-workbench-composer">
                <Space direction="vertical" size={10} className="full">
                  <Space wrap>
                    <Select
                      mode="multiple"
                      value={workbenchQuestionTypes}
                      onChange={(value) => setWorkbenchQuestionTypes(value as Question["question_type"][])}
                      options={[
                        { value: "single_choice", label: "选择" },
                        { value: "true_false", label: "判断" },
                        { value: "fill_blank", label: "填空" },
                      ]}
                      disabled={assistantIntent === "repair_question" || workbenchStreaming || !questionWorkbenchGate.healthy}
                      className="ai-workbench-type-select"
                    />
                    <InputNumber
                      min={1}
                      max={20}
                      value={workbenchCount}
                      onChange={(value) => setWorkbenchCount(Number(value || 1))}
                      addonBefore="数量"
                      disabled={assistantIntent === "repair_question" || workbenchStreaming || !questionWorkbenchGate.healthy}
                    />
                  </Space>
                  <Input.TextArea
                    rows={4}
                    value={workbenchPrompt}
                    disabled={workbenchStreaming || !questionWorkbenchGate.healthy}
                    onChange={(event) => setWorkbenchPrompt(event.target.value)}
                    placeholder="可以连续追问，例如：保留原实验点位，把选项 B 改成更有诊断价值的误区。"
                  />
                </Space>
              </div>
            </section>

            <section className="ai-workbench-panel ai-workbench-candidates">
              <Flex justify="space-between" align="center" gap={10} className="ai-workbench-section-head">
                <div>
                  <Text className="eyebrow">候选版本</Text>
                  <Title level={4}>建议草稿</Title>
                </div>
                <Tag>{workbenchCandidates.length} 条</Tag>
              </Flex>
              <div className="ai-workbench-candidate-list">
                {workbenchCandidates.length ? (
                  workbenchCandidates.map((candidate) => {
                    const payload = candidatePayload(candidate);
                    const errors = candidateValidationErrors(candidate);
                    return (
                      <div key={candidate.id} className="ai-candidate-card">
                        <Space direction="vertical" size={8} className="full">
                          <Flex justify="space-between" align="start" gap={8}>
                            <Space size={4} wrap>
                              <Tag color="blue">{questionTypeLabel(candidateQuestionType(candidate))}</Tag>
                              {errors.length ? <Tag color="red">需修订</Tag> : <Tag color="green">可发布</Tag>}
                              {candidate.status !== "draft" ? <Tag>{candidate.status}</Tag> : null}
                            </Space>
                            <Text type="secondary">{candidate.id.slice(0, 8)}</Text>
                          </Flex>
                          <Text strong>{candidateStem(candidate) || "未生成题干"}</Text>
                          {Array.isArray(payload.options) && payload.options.length ? (
                            <div className="question-options">
                              {payload.options.map((option, index) => {
                                const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
                                const text = typeof option === "string" ? option : option.text || "";
                                return (
                                  <div key={`${candidate.id}-${label}-${index}`} className="question-option">
                                    <Text strong>{label}</Text>
                                    <Text>{text}</Text>
                                  </div>
                                );
                              })}
                            </div>
                          ) : null}
                          <Descriptions size="small" column={1} className="question-workbench-descriptions">
                            <Descriptions.Item label="答案">{answerText(payload.answer as Record<string, unknown>)}</Descriptions.Item>
                            <Descriptions.Item label="解析">{String(payload.explanation || "暂无解析")}</Descriptions.Item>
                          </Descriptions>
                          <Space size={4} wrap>
                            {candidateQuestionPoints(candidate).slice(0, 3).map((point) => (
                              <Tag key={point.point_key || point.point_title} color="cyan">
                                {point.point_title || point.point_key}
                              </Tag>
                            ))}
                          </Space>
                          {errors.length ? <Alert type="warning" showIcon message={errors.join("；")} /> : null}
                          <Flex justify="space-between" align="center" gap={8} wrap="wrap">
                            <Button
                              size="small"
                              onClick={() => setWorkbenchPrompt(`请继续修订候选 ${candidate.id.slice(0, 8)}：`)}
                            >
                              继续修
                            </Button>
                            <Space size={4}>
                              <Popconfirm
                                title="发布这条候选？"
                                onConfirm={() => publishCandidate.mutate(candidate.id)}
                                disabled={Boolean(errors.length) || candidate.status !== "draft"}
                              >
                                <Button
                                  type="link"
                                  size="small"
                                  disabled={Boolean(errors.length) || candidate.status !== "draft"}
                                  loading={publishCandidate.isPending}
                                >
                                  发布
                                </Button>
                              </Popconfirm>
                              <Button
                                type="link"
                                danger
                                size="small"
                                disabled={candidate.status !== "draft"}
                                loading={rejectCandidate.isPending}
                                onClick={() => rejectCandidate.mutate(candidate.id)}
                              >
                                拒绝
                              </Button>
                            </Space>
                          </Flex>
                        </Space>
                      </div>
                    );
                  })
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无候选，先发送一条提示" />
                )}
              </div>
            </section>
          </div>
        </QueryState>
      </Drawer>
    </Space>
  );
}
