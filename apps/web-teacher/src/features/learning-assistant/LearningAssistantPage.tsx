import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Descriptions,
  Empty,
  Flex,
  Form,
  Input,
  Progress,
  Select,
  Space,
  Spin,
  Statistic,
  Switch,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import {
  ArrowRightOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";

import type { Experiment } from "../../api/experiments";
import type { AIConfiguration } from "../../api/settings";
import type { LearningAssistantAskRequest, LearningAssistantResponse, LearningAssistantRuntime, LearningAssistantSource } from "../../api/learningAssistant";
import { getAuthToken } from "../../api/auth";
import { api, apiBase, postJsonStream } from "../../api/http";
import { AIGlowButton } from "../../components/AIGlowButton";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { useAdminChapters as useChapters, useAdminExperiments as useExperiments } from "../../lib/adminCatalogHooks";
import { experimentVideoCandidates, formatChapterTitle, isGeneralResourceTitle } from "../../lib/resourceUtils";
import { errorMessage } from "../../lib/errors";
import { formatMemoryMb, formatRuntimeSeconds, formatTraceMs, warmupStatusLabel } from "../../lib/runtimeFormat";
import "./learning-assistant.css";

const { Text, Title } = Typography;
const LazyAssistantMarkdownContent = lazy(async () => {
  const module = await import("../../lib/assistant-markdown");
  return { default: module.AssistantMarkdownContent };
});

function renderAssistantInlineMarkdown(text: string | null | undefined): ReactNode {
  return (
    <Suspense fallback={null}>
      <LazyAssistantMarkdownContent text={text} inline />
    </Suspense>
  );
}

function renderAssistantMarkdown(text: string | null | undefined): ReactNode {
  return (
    <Suspense fallback={null}>
      <LazyAssistantMarkdownContent text={text} />
    </Suspense>
  );
}

type LearningAssistantFormValues = Omit<
  LearningAssistantAskRequest,
  "question" | "knowledge_point_ids" | "conversation_history" | "max_answer_chars"
>;

type LearningAssistantTurn = {
  id: string;
  question: string;
  answer: string;
  response?: LearningAssistantResponse;
  status: "running" | "done" | "error";
  streamStatus?: string;
  error?: string;
  createdAt: string;
};

type LearningAssistantPointContext = {
  chapterId?: string | null;
  experimentId?: string | null;
  experimentCode?: string | null;
  experimentTitle?: string | null;
  pointKey?: string | null;
  pointTitle?: string | null;
  pointIndex?: number | null;
};

type LearningAssistantPointOption = {
  pointKey: string;
  pointTitle: string;
  pointIndex: number;
};

type LearningAssistantPointIntent = {
  id: string;
  label: string;
  description: string;
  buildQuestion?: (context: LearningAssistantPointContext) => string;
};

const learningAssistantPolicyLabels: Record<string, string> = {
  normal_answer: "普通回答",
  refuse_out_of_scope: "课程外拒答",
  safe_experiment_guidance: "实验安全引导",
  assessment_hint: "测验提示",
  needs_platform_evidence: "资源可用性",
};

const learningAssistantModeLabels: Record<string, string> = {
  local: "本地兜底",
  guardrail_refusal: "护栏拒答",
  guardrail_hint: "护栏提示",
  openai_chat_fallback: "普通模型",
  openai_chat_stream: "流式模型",
  openai_agents_sdk: "模型回答",
};

const learningAssistantGuardrailLabels: Record<string, string> = {
  agent_sdk_fallback: "模型兜底",
  assessment_answer_leakage: "测验保护",
  chat_completion_fallback: "普通模型兜底",
  chat_completion_stream_fallback: "流式模型兜底",
  course_scope: "课程范围",
  experiment_safety: "实验安全",
  missing_evidence: "缺少证据",
  no_fabricated_resource: "资源未发布",
  point_context_empty: "点位证据为空",
  point_context_fixed: "固定点位证据",
  point_context_missing_reviewed_evidence: "点位证据缺失",
  policy_decision_invalid: "策略兜底",
  policy_gate_fallback: "策略兜底",
  rag_no_match: "RAG 未命中",
  rag_lookup_disabled: "RAG 关闭",
  simple_greeting: "简单问候",
  source_grounding: "来源约束",
  mobile_length: "长度控制",
};

const learningAssistantActionLabels: Record<string, string> = {
  allow_without_tools: "无需工具",
  answer_without_rag: "无 RAG 回答",
  continue_with_local_policy: "走本地策略",
  fallback_to_local: "转本地兜底",
  answer_from_model_knowledge: "用模型常识",
  no_evidence_fallback: "说明无证据",
  override_no_evidence: "覆盖无来源回答",
  override_unavailable_resource: "资源未发布",
  provide_hint: "只给提示",
  refuse: "拒答",
  refuse_unsafe_detail: "拒绝危险步骤",
  skip_rag_lookup: "跳过 RAG",
  state_unavailable: "资源未发布",
  trim: "截断",
  use_fixed_evidence: "使用固定证据",
};

function createStreamingAssistantResponse(answer = ""): LearningAssistantResponse {
  return {
    answer,
    sources: [],
    mode: "openai_chat_stream",
    classification: {},
    tool_calls: [],
    guardrail_decisions: [],
    rag_trace: {},
    review_required: true,
  };
}

function assistantConversationHistory(turns: LearningAssistantTurn[]) {
  return turns
    .filter((turn) => turn.question.trim() || turn.answer.trim())
    .flatMap((turn) => [
      { role: "user" as const, content: turn.question },
      ...(turn.answer.trim() ? [{ role: "assistant" as const, content: turn.answer }] : []),
    ])
    .slice(-10);
}

function assistantTurnLabel(turn: LearningAssistantTurn, index: number) {
  return `第 ${index + 1} 轮`;
}

function assistantResponseTypeLabel(turn: LearningAssistantTurn) {
  const response = turn.response;
  const mode = String(response?.classification?.policy_decision_mode || response?.classification?.intent || "");
  const labels: Record<string, string> = {
    normal_answer: "普通回答",
    course_factual_query: "课程问答",
    assessment_guidance: "测验保护",
    unsafe_experiment: "安全拦截",
    resource_request: "资源可用性",
    out_of_scope: "范围外",
    greeting: "问候",
  };
  return labels[mode] || learningAssistantPolicyLabels[mode] || mode;
}

function assistantStreamPhaseLabel(status?: string, hasAnswer = false) {
  if (hasAnswer) return "正在生成回答";
  const text = String(status || "");
  if (text.includes("判断") || text.includes("安全") || text.includes("策略")) return "正在检查问题策略";
  if (text.includes("检索") || text.includes("RAG") || text.includes("证据")) return "正在检索课程证据";
  if (text.includes("连接") || text.includes("模型") || text.includes("流式")) return "正在连接模型";
  if (text.includes("兜底")) return "正在切换兜底回答";
  return text || "正在准备回答";
}

function assistantChapterExperiments(experiments: Experiment[], chapterId?: string | null) {
  const selectedChapterId = String(chapterId || "").trim();
  const visible = experiments.filter((experiment) => experiment.status !== "archived");
  if (!selectedChapterId) return visible;
  return visible.filter((experiment) => (
    experiment.chapter_bindings || []
  ).some((binding) => binding.chapter_id === selectedChapterId));
}

function sha1Hex(value: string) {
  const bytes = Array.from(new TextEncoder().encode(value.trim()));
  const bitLength = bytes.length * 8;
  bytes.push(0x80);
  while (bytes.length % 64 !== 56) bytes.push(0);
  for (let shift = 56; shift >= 0; shift -= 8) {
    bytes.push(Math.floor(bitLength / 2 ** shift) & 0xff);
  }

  let h0 = 0x67452301;
  let h1 = 0xefcdab89;
  let h2 = 0x98badcfe;
  let h3 = 0x10325476;
  let h4 = 0xc3d2e1f0;

  const rotateLeft = (num: number, bits: number) => ((num << bits) | (num >>> (32 - bits))) >>> 0;
  for (let offset = 0; offset < bytes.length; offset += 64) {
    const words = new Array<number>(80).fill(0);
    for (let index = 0; index < 16; index += 1) {
      const base = offset + index * 4;
      words[index] = (
        (bytes[base] << 24)
        | (bytes[base + 1] << 16)
        | (bytes[base + 2] << 8)
        | bytes[base + 3]
      ) >>> 0;
    }
    for (let index = 16; index < 80; index += 1) {
      words[index] = rotateLeft(words[index - 3] ^ words[index - 8] ^ words[index - 14] ^ words[index - 16], 1);
    }

    let a = h0;
    let b = h1;
    let c = h2;
    let d = h3;
    let e = h4;
    for (let index = 0; index < 80; index += 1) {
      let f = 0;
      let k = 0;
      if (index < 20) {
        f = (b & c) | (~b & d);
        k = 0x5a827999;
      } else if (index < 40) {
        f = b ^ c ^ d;
        k = 0x6ed9eba1;
      } else if (index < 60) {
        f = (b & c) | (b & d) | (c & d);
        k = 0x8f1bbcdc;
      } else {
        f = b ^ c ^ d;
        k = 0xca62c1d6;
      }
      const temp = (rotateLeft(a, 5) + f + e + k + words[index]) >>> 0;
      e = d;
      d = c;
      c = rotateLeft(b, 30);
      b = a;
      a = temp;
    }
    h0 = (h0 + a) >>> 0;
    h1 = (h1 + b) >>> 0;
    h2 = (h2 + c) >>> 0;
    h3 = (h3 + d) >>> 0;
    h4 = (h4 + e) >>> 0;
  }

  return [h0, h1, h2, h3, h4].map((word) => word.toString(16).padStart(8, "0")).join("");
}

function learningAssistantCandidatePointKey(index: number, title: string) {
  return `candidate-${index + 1}-${sha1Hex(title).slice(0, 8)}`;
}

function learningAssistantExperimentLabel(experiment?: Experiment | null) {
  if (!experiment) return "-";
  return [experiment.code, experiment.title].map((item) => String(item || "").trim()).filter(Boolean).join(" · ")
    || experiment.id;
}

function learningAssistantPointOptions(experiment?: Experiment | null): LearningAssistantPointOption[] {
  const candidates = experimentVideoCandidates(experiment);
  if (candidates.length) {
    return candidates.map((pointTitle, index) => ({
      pointKey: learningAssistantCandidatePointKey(index, pointTitle),
      pointTitle,
      pointIndex: index + 1,
    }));
  }

  const byKey = new Map<string, LearningAssistantPointOption>();
  for (const resource of experiment?.media_resources || []) {
    const key = String(resource.point_key || resource.point_title || "").trim();
    if (!key || byKey.has(key)) continue;
    byKey.set(key, {
      pointKey: key,
      pointTitle: String(resource.point_title || resource.title || resource.original_file_name || key).trim(),
      pointIndex: byKey.size + 1,
    });
  }
  return [...byKey.values()];
}

function learningAssistantPointContext(
  chapterId: string | null | undefined,
  experiment: Experiment,
  point: LearningAssistantPointOption,
): LearningAssistantPointContext {
  return {
    chapterId: chapterId || null,
    experimentId: experiment.id,
    experimentCode: experiment.code,
    experimentTitle: experiment.title,
    pointKey: point.pointKey,
    pointTitle: point.pointTitle,
    pointIndex: point.pointIndex,
  };
}

const learningAssistantPointIntents: LearningAssistantPointIntent[] = [
  {
    id: "observe",
    label: "观察什么",
    description: "聚焦操作对象和观察目标",
    buildQuestion: (context) => `我正在看「${context.experimentCode ? `${context.experimentCode} ` : ""}${context.experimentTitle || "这个实验"}」的点位 ${context.pointIndex || ""}「${context.pointTitle || context.pointKey || ""}」。这个点位主要要观察什么？`,
  },
  {
    id: "phenomenon",
    label: "现象说明什么",
    description: "把现象和结论连起来",
    buildQuestion: (context) => `请结合「${context.pointTitle || context.pointKey || "这个点位"}」这个视频点位，说明可能观察到的现象分别说明什么。`,
  },
  {
    id: "principle",
    label: "背后原理",
    description: "解释对应化学原理",
    buildQuestion: (context) => `请解释「${context.pointTitle || context.pointKey || "这个点位"}」背后的化学原理，并说明它和本实验结论的关系。`,
  },
  {
    id: "design",
    label: "为什么这样设计",
    description: "理解试剂和步骤安排",
    buildQuestion: (context) => `为什么本实验要设置「${context.pointTitle || context.pointKey || "这个点位"}」这个点位？这种实验设计想证明什么？`,
  },
  {
    id: "compare",
    label: "和其他点位对比",
    description: "放回同一实验里比较",
    buildQuestion: (context) => `请把「${context.pointTitle || context.pointKey || "这个点位"}」放回「${context.experimentCode || ""} ${context.experimentTitle || "本实验"}」中，和相邻点位对比说明它的作用。`,
  },
  {
    id: "mistake",
    label: "易错点",
    description: "找常见误解和判断边界",
    buildQuestion: (context) => `学习「${context.pointTitle || context.pointKey || "这个点位"}」时容易误解哪里？请结合本实验证据帮我梳理易错点。`,
  },
  {
    id: "custom",
    label: "我自己问",
    description: "保留点位上下文，手动输入",
  },
];

function getRagTraceLatest(response?: LearningAssistantResponse) {
  const trace = response?.rag_trace || {};
  const latest = (trace as { latest?: unknown }).latest;
  return latest && typeof latest === "object" ? (latest as Record<string, unknown>) : {};
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function traceRecord(trace: Record<string, unknown>, key: string): Record<string, unknown> {
  return asRecord(trace[key]);
}

function traceRecords(trace: Record<string, unknown>, key: string): Record<string, unknown>[] {
  const value = trace[key];
  return Array.isArray(value)
    ? value.filter((item) => item && typeof item === "object").map((item) => item as Record<string, unknown>)
    : [];
}

function traceNumber(value: unknown): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function warmupStatusColor(status?: string) {
  if (status === "succeeded") return "#005826";
  if (status === "running") return "blue";
  if (status === "failed") return "red";
  return "default";
}

function sourceKindLabel(value: unknown): string {
  const source = String(value || "");
  const labels: Record<string, string> = {
    keyword: "关键词召回",
    keyword_generated: "生成 Query 关键词",
    vector: "BGE 向量召回",
  };
  return labels[source] || source || "未知来源";
}

function findFinalEvidence(source: LearningAssistantSource, finalEvidence: Record<string, unknown>[]) {
  return finalEvidence.find((item) => String(item.chunk_id || "") === source.chunk_id);
}

function RagAssetPreview({ asset }: { asset: NonNullable<LearningAssistantSource["assets"]>[number] }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    const controller = new AbortController();
    let objectUrl: string | null = null;
    setSrc(null);
    setFailed(false);

    fetch(`${apiBase}/api/admin/rag-assets?path=${encodeURIComponent(asset.path)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch((error) => {
        if ((error as Error).name !== "AbortError") {
          setFailed(true);
        }
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [asset.path]);

  if (failed) {
    return (
      <div className="assistant-source-asset assistant-source-asset-failed">
        <Text type="secondary">{asset.file_name || "图像资产不可访问"}</Text>
      </div>
    );
  }

  return (
    <div className="assistant-source-asset">
      {src ? (
        <img src={src} alt={asset.caption || asset.file_name || "RAG 图像证据"} />
      ) : (
        <div className="assistant-source-asset-loading" />
      )}
      <span>{asset.kind === "page" ? "整页" : "图像"} · {asset.file_name}</span>
    </div>
  );
}

export function LearningAssistantPage() {
  const { message } = AntApp.useApp();
  const chatDraftMaxLength = 1024;
  const [form] = Form.useForm<LearningAssistantFormValues>();
  const [turns, setTurns] = useState<LearningAssistantTurn[]>([]);
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [chatDraft, setChatDraft] = useState("");
  const [assistantStreaming, setAssistantStreaming] = useState(false);
  const [starterExperimentId, setStarterExperimentId] = useState<string | null>(null);
  const [starterPointKey, setStarterPointKey] = useState<string | null>(null);
  const [starterIntentId, setStarterIntentId] = useState<string>(learningAssistantPointIntents[0].id);
  const [activePointContext, setActivePointContext] = useState<LearningAssistantPointContext | null>(null);
  const chatListRef = useRef<HTMLDivElement | null>(null);
  const chapters = useChapters();
  const experiments = useExperiments("?limit=200");
  const selectedChapterId = (Form.useWatch("chapter_id", form) as string | undefined) || "CH13";
  const experimentItems = experiments.data?.items || [];
  const aiConfig = useQuery({
    queryKey: ["ai-configuration", "learning-assistant"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });
  const assistantRuntime = useQuery({
    queryKey: ["learning-assistant-runtime", "learning-assistant-status"],
    queryFn: () => api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime"),
    refetchInterval: 10000,
  });
  const selectedTurn = turns.find((turn) => turn.id === selectedTurnId) || turns.at(-1);

  useEffect(() => {
    chatListRef.current?.scrollTo({ top: chatListRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  useEffect(() => {
    setStarterExperimentId(null);
    setStarterPointKey(null);
    setStarterIntentId(learningAssistantPointIntents[0].id);
    setActivePointContext(null);
    setChatDraft("");
  }, [selectedChapterId]);

  const starterExperiments = useMemo(
    () => assistantChapterExperiments(experimentItems, selectedChapterId),
    [experimentItems, selectedChapterId],
  );
  const starterExperiment = starterExperiments.find((experiment) => experiment.id === starterExperimentId)
    || starterExperiments[0]
    || null;
  const starterPointOptions = useMemo(
    () => learningAssistantPointOptions(starterExperiment),
    [starterExperiment],
  );
  const starterPoint = starterPointOptions.find((point) => point.pointKey === starterPointKey)
    || starterPointOptions[0]
    || null;
  const starterIntent = learningAssistantPointIntents.find((intent) => intent.id === starterIntentId)
    || learningAssistantPointIntents[0];
  const starterPointContext = starterExperiment && starterPoint
    ? learningAssistantPointContext(selectedChapterId, starterExperiment, starterPoint)
    : null;
  const starterQuestion = starterPointContext && starterIntent.buildQuestion
    ? starterIntent.buildQuestion(starterPointContext)
    : "";
  const starterLaunchDisabled = assistantStreaming || !starterPointContext || (!chatDraft.trim() && !starterQuestion);
  const starterPointTotal = useMemo(
    () => starterExperiments.reduce((total, experiment) => total + learningAssistantPointOptions(experiment).length, 0),
    [starterExperiments],
  );

  useEffect(() => {
    setStarterExperimentId((current) => {
      if (current && starterExperiments.some((experiment) => experiment.id === current)) return current;
      return starterExperiments[0]?.id || null;
    });
  }, [starterExperiments]);

  useEffect(() => {
    setStarterPointKey((current) => {
      if (current && starterPointOptions.some((point) => point.pointKey === current)) return current;
      return starterPointOptions[0]?.pointKey || null;
    });
  }, [starterPointOptions]);

  const submit = async (
    questionInput?: string,
    pointContext?: LearningAssistantPointContext,
  ) => {
    const question = String(questionInput ?? chatDraft).trim();
    if (!question) {
      message.warning("请输入学生问题");
      return;
    }
    const values = form.getFieldsValue(true) as LearningAssistantFormValues;
    const chapterId = values.chapter_id || selectedChapterId;
    if (!chapterId) {
      message.warning("请选择章节范围");
      return;
    }
    const contextForRequest = pointContext ?? activePointContext;
    const payload: LearningAssistantAskRequest = {
      question,
      student_id: values.student_id?.trim() || null,
      chapter_id: chapterId,
      experiment_id: contextForRequest?.experimentId || null,
      point_key: contextForRequest?.pointKey || null,
      knowledge_point_ids: [],
      allow_progress_lookup: values.allow_progress_lookup ?? true,
      allow_rag_lookup: values.allow_rag_lookup ?? true,
      conversation_history: assistantConversationHistory(turns),
      max_answer_chars: 0,
    };

    const turnId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const nextTurn: LearningAssistantTurn = {
      id: turnId,
      question: payload.question,
      answer: "",
      response: createStreamingAssistantResponse(),
      status: "running",
      streamStatus: "正在连接学习助手",
      createdAt: new Date().toISOString(),
    };
    setAssistantStreaming(true);
    setChatDraft("");
    if (pointContext) {
      setActivePointContext(pointContext);
    }
    setTurns((current) => [...current, nextTurn]);
    setSelectedTurnId(turnId);
    try {
      await postJsonStream<{
        message?: string;
        delta?: string;
        answer?: string;
        response?: LearningAssistantResponse;
      }>("/api/admin/learning-assistant/ask/stream", payload, ({ event, data }) => {
        if (event === "status") {
          setTurns((current) => current.map((turn) => (
            turn.id === turnId ? { ...turn, streamStatus: String(data.message || "学习助手正在生成") } : turn
          )));
        }
        if (event === "delta" && data.delta) {
          setTurns((current) => current.map((turn) => {
            if (turn.id !== turnId) return turn;
            const nextAnswer = `${turn.answer}${data.delta}`;
            return {
              ...turn,
              answer: nextAnswer,
              response: { ...(turn.response || createStreamingAssistantResponse()), answer: nextAnswer },
            };
          }));
        }
        if (event === "replace") {
          const answer = String(data.answer || "");
          setTurns((current) => current.map((turn) => (
            turn.id === turnId
              ? { ...turn, answer, response: { ...(turn.response || createStreamingAssistantResponse()), answer } }
              : turn
          )));
        }
        if (event === "final" && data.response) {
          setTurns((current) => current.map((turn) => (
            turn.id === turnId
              ? { ...turn, answer: data.response?.answer || turn.answer, response: data.response, status: "done", streamStatus: "" }
              : turn
          )));
          message.success("学习助手已返回");
        }
        if (event === "error") {
          throw new Error(String(data.message || "学习助手生成失败"));
        }
      });
    } catch (error) {
      setTurns((current) => current.map((turn) => (
        turn.id === turnId ? { ...turn, status: "error", error: errorMessage(error), streamStatus: "" } : turn
      )));
      message.error(errorMessage(error));
    } finally {
      setAssistantStreaming(false);
    }
  };

  const applyStarterIntent = (intent: LearningAssistantPointIntent) => {
    setStarterIntentId(intent.id);
  };
  const submitStarterQuestion = async () => {
    if (!starterPointContext) {
      message.warning("请先选择实验点位");
      return;
    }
    const question = (chatDraft.trim() || starterQuestion).trim();
    if (!question) {
      message.info("请先输入问题或选择一个提问方向");
      return;
    }
    await submit(question, starterPointContext);
  };
  const assistantChapterOptions = (chapters.data || [])
    .filter((chapter) => !isGeneralResourceTitle(chapter.chapter_title, chapter.chapter_id))
    .map((chapter) => ({
      value: chapter.chapter_id,
      label: formatChapterTitle(chapter.chapter_title, chapter.chapter_id),
    }));
  const response = selectedTurn?.response;
  const selectedTurnIndex = selectedTurn ? turns.findIndex((turn) => turn.id === selectedTurn.id) : -1;
  const policyMode = String(response?.classification?.policy_decision_mode || response?.classification?.intent || "");
  const policyLabel = learningAssistantPolicyLabels[policyMode] || policyMode || "-";
  const modeLabel = response?.mode ? learningAssistantModeLabels[response.mode] || response.mode : "-";
  const connectionStatus = aiConfig.data?.status.connectivity_status || "not_configured";
  const ragRuntime = assistantRuntime.data?.rag_runtime || aiConfig.data?.rag_runtime;
  const bgeMetrics = assistantRuntime.data?.bge_metrics || null;
  const bgeStatus = assistantRuntime.data?.bge_status
    || (assistantRuntime.data?.bge_error
      ? "unreachable"
      : bgeMetrics?.ok
        ? "healthy"
        : bgeMetrics
          ? "degraded"
          : ragRuntime?.bge_service_required
            ? "checking"
            : "not_required");
  const latestRagTrace = getRagTraceLatest(response);
  const pointContextTrace = traceRecord(response?.rag_trace || {}, "point_context");
  const pointContextEnabled = pointContextTrace.enabled === true || Boolean(pointContextTrace.point_key || pointContextTrace.requested_point_key);
  const pointContextSources = traceRecords(pointContextTrace, "sources");
  const pointContextChunkIds = Array.isArray(pointContextTrace.chunk_ids)
    ? pointContextTrace.chunk_ids.map((item) => String(item)).filter(Boolean)
    : [];
  const pointContextExperimentChunkIds = Array.isArray(pointContextTrace.experiment_chunk_ids)
    ? pointContextTrace.experiment_chunk_ids.map((item) => String(item)).filter(Boolean)
    : [];
  const pointContextTheoryChunkIds = Array.isArray(pointContextTrace.theory_chunk_ids)
    ? pointContextTrace.theory_chunk_ids.map((item) => String(item)).filter(Boolean)
    : [];
  const pointContextMissingChunkIds = Array.isArray(pointContextTrace.missing_chunk_ids)
    ? pointContextTrace.missing_chunk_ids.map((item) => String(item)).filter(Boolean)
    : [];
  const pointContextEvidenceSource = String(pointContextTrace.evidence_source || "");
  const pointContextReviewGrade = String(pointContextTrace.review_grade || "");
  const pointContextExperimentSourceCount = traceNumber(pointContextTrace.experiment_source_count);
  const pointContextTheorySourceCount = traceNumber(pointContextTrace.theory_source_count);
  const pointContextSourceCount = traceNumber(pointContextTrace.source_count);
  const traceTimings = traceRecord(latestRagTrace, "timings_ms");
  const traceCounts = traceRecord(latestRagTrace, "candidate_counts");
  const finalEvidence = traceRecords(latestRagTrace, "final_evidence");
  const keywordTotalCount = traceNumber(traceCounts.keyword_total);
  const vectorCount = traceNumber(traceCounts.vector);
  const mergedCount = traceNumber(traceCounts.merged);
  const rerankPoolCount = traceNumber(traceCounts.rerank_pool);
  const finalEvidenceCount = traceNumber(traceCounts.final);
  const traceReranked = latestRagTrace.rerank_applied === true || latestRagTrace.mode === "hybrid_bge_rerank";
  const chatDraftLength = chatDraft.length;
  const chatDraftAtLimit = chatDraftLength >= chatDraftMaxLength;
  const connectionLabels: Record<string, string> = {
    connected: "已连接",
    failed: "连接失败",
    not_configured: "未配置",
    stale: "需复检",
    untested: "待检测",
  };
  const ragHealthMeta = (() => {
    if (!ragRuntime?.rag_enabled) return { value: "关闭", tone: "muted" };
    if (!ragRuntime.hybrid_bge_enabled) return { value: "健康", tone: "ok" };
    if (bgeStatus === "healthy") return { value: "健康", tone: "ok" };
    if (bgeStatus === "checking") return { value: "检测中", tone: "warn" };
    if (bgeStatus === "degraded") return { value: "降级", tone: "warn" };
    if (bgeStatus === "unreachable" || bgeStatus === "not_configured") return { value: "异常", tone: "bad" };
    return { value: "待检测", tone: "warn" };
  })();
  const ragModeMeta = (() => {
    if (!ragRuntime?.rag_enabled) return { value: "关闭", tone: "muted" };
    if (ragRuntime.hybrid_bge_enabled) return { value: "混合", tone: "ok" };
    return { value: "关键词", tone: "warn" };
  })();
  const assistantStatusChips = [
    {
      label: "模型",
      value: connectionLabels[connectionStatus] || connectionStatus,
      tone: connectionStatus === "connected" ? "ok" : connectionStatus === "failed" ? "bad" : "muted",
    },
    {
      label: "RAG 状态",
      value: ragHealthMeta.value,
      tone: ragHealthMeta.tone,
    },
    {
      label: "RAG 模式",
      value: ragModeMeta.value,
      tone: ragModeMeta.tone,
    },
  ];

  return (
    <Space orientation="vertical" size={18} className="full">
      <PageTitle
        title="学习助手"
        description="模拟学生学习页 chat，验证课程范围、实验安全、测验保护和来源证据策略。"
        extra={<Tag color="#005826">学生场景测试</Tag>}
      />
      <div className="assistant-status-strip assistant-status-bar">
        {assistantStatusChips.map((item) => (
          <div key={item.label} className={`assistant-status-chip assistant-status-chip-${item.tone}`}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
      <div className="learning-assistant-workbench">
        <Card title="上下文设置" className="learning-assistant-card learning-assistant-context">
          <Text type="secondary" className="assistant-context-note">
            学生端从章节学习页进入；实验和视频点位由章节内容中的起始问题带入。
          </Text>
          <Form
            form={form}
            layout="vertical"
            initialValues={{ chapter_id: "CH13", allow_progress_lookup: true, allow_rag_lookup: true }}
          >
            <div className="settings-grid">
              <Form.Item name="student_id" label="学生学号">
                <Input placeholder="可选，用于测试本人学习进度" />
              </Form.Item>
              <Form.Item name="chapter_id" label="章节范围">
                <Select
                  showSearch
                  placeholder="选择章节"
                  optionFilterProp="label"
                  loading={chapters.isLoading}
                  options={assistantChapterOptions}
                />
              </Form.Item>
            </div>
            <div className="assistant-switch-row">
              <Form.Item name="allow_rag_lookup" valuePropName="checked" noStyle>
                <Switch checkedChildren="RAG" unCheckedChildren="RAG" />
              </Form.Item>
              <Text type="secondary">允许本次检索课程证据</Text>
              <Form.Item name="allow_progress_lookup" valuePropName="checked" noStyle>
                <Switch checkedChildren="进度" unCheckedChildren="进度" />
              </Form.Item>
              <Text type="secondary">允许查询该学生本人进度</Text>
            </div>
          </Form>
        </Card>

        <Card
          title="多轮对话"
          className="learning-assistant-card learning-assistant-chat"
          extra={
            <Space size={8}>
              <Text type="secondary">{turns.length} 轮</Text>
              <Button
                size="small"
                onClick={() => {
                  setTurns([]);
                  setSelectedTurnId(null);
                  setActivePointContext(null);
                }}
                disabled={!turns.length || assistantStreaming}
              >
                清空
              </Button>
            </Space>
          }
        >
          <div className="assistant-chat-shell">
            <div className="assistant-chat-scroll" ref={chatListRef}>
              {turns.length ? (
                <div className="assistant-chat-list">
                  {turns.map((turn, index) => (
                    <button
                      type="button"
                      key={turn.id}
                      className={`assistant-turn ${selectedTurn?.id === turn.id ? "selected" : ""}`}
                      onClick={() => setSelectedTurnId(turn.id)}
                    >
                      <div className="assistant-message user">
                        <div className="assistant-message-meta">
                          <Text strong>学生</Text>
                          <Text type="secondary">{dayjs(turn.createdAt).format("HH:mm:ss")}</Text>
                        </div>
                        <div>{turn.question}</div>
                      </div>
                      <div className={`assistant-message assistant ${turn.status}`}>
                        <div className="assistant-message-meta">
                          <Space size={8} wrap>
                            <Text strong>学习助手</Text>
                            <Tag className={`assistant-response-chip assistant-response-chip-${turn.status}`}>
                              {turn.status === "done" ? "完成" : turn.status === "error" ? "失败" : "生成中"}
                            </Tag>
                            {assistantResponseTypeLabel(turn) ? (
                              <Tag className="assistant-response-chip">{assistantResponseTypeLabel(turn)}</Tag>
                            ) : null}
                          </Space>
                          <Text type="secondary" className="assistant-turn-index">{assistantTurnLabel(turn, index)}</Text>
                        </div>
                        {turn.status === "running" ? (
                          <div className="assistant-stream-progress">
                            <span className="assistant-stream-dots" aria-hidden="true">
                              <span />
                              <span />
                              <span />
                            </span>
                            <span>{assistantStreamPhaseLabel(turn.streamStatus, Boolean(turn.answer))}</span>
                          </div>
                        ) : null}
                        {turn.error ? <div className="assistant-error-line">{turn.error}</div> : null}
                        <div className={`assistant-answer ${turn.answer ? "" : "assistant-answer-empty"}`}>
                          {turn.answer ? renderAssistantMarkdown(turn.answer) : (
                            turn.status === "running" ? (
                              <div className="assistant-stream-skeleton">
                                <span />
                                <span />
                              </div>
                            ) : renderAssistantMarkdown("等待模型输出...")
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="assistant-empty-start assistant-starter-panel">
                  <div className="assistant-starter-heading">
                    <div className="assistant-empty-title">从本章实验点位开始提问</div>
                    <Text type="secondary">
                      章节范围由左侧选择；这里选择实验、点位和想问的方向，发送后继续正常多轮对话。
                    </Text>
                  </div>
                  {experiments.isLoading ? (
                    <Spin description="正在读取本章实验点位" />
                  ) : starterPointTotal ? (
                    <>
                      <div className="assistant-starter-grid">
                        <section className="assistant-starter-column">
                          <div className="assistant-starter-section-title">1. 选择实验</div>
                          <div className="assistant-starter-list">
                            {starterExperiments.map((experiment) => {
                              const pointCount = learningAssistantPointOptions(experiment).length;
                              const selected = starterExperiment?.id === experiment.id;
                              return (
                                <button
                                  type="button"
                                  key={experiment.id}
                                  className={`assistant-starter-option ${selected ? "selected" : ""}`}
                                  onClick={() => {
                                    setStarterExperimentId(experiment.id);
                                    setStarterPointKey(null);
                                    setStarterIntentId(learningAssistantPointIntents[0].id);
                                    setChatDraft("");
                                  }}
                                  disabled={assistantStreaming}
                                >
                                  <span className="assistant-starter-option-title">
                                    {experiment.code || experiment.title || experiment.id}
                                  </span>
                                  <span className="assistant-starter-option-meta">{experiment.title || experiment.id}</span>
                                  <span className="assistant-starter-option-badge">{pointCount} 点位</span>
                                </button>
                              );
                            })}
                          </div>
                        </section>

                        <section className="assistant-starter-column">
                          <div className="assistant-starter-section-title">2. 选择点位</div>
                          {starterPointOptions.length ? (
                            <div className="assistant-starter-list">
                              {starterPointOptions.map((point) => {
                                const selected = starterPoint?.pointKey === point.pointKey;
                                return (
                                  <button
                                    type="button"
                                    key={point.pointKey}
                                    className={`assistant-starter-option ${selected ? "selected" : ""}`}
                                  onClick={() => {
                                    setStarterPointKey(point.pointKey);
                                    setStarterIntentId(learningAssistantPointIntents[0].id);
                                    setChatDraft("");
                                  }}
                                    disabled={assistantStreaming}
                                  >
                                    <span className="assistant-starter-option-title">点位 {point.pointIndex}</span>
                                    <span className="assistant-starter-option-meta">{point.pointTitle}</span>
                                  </button>
                                );
                              })}
                            </div>
                          ) : (
                            <Text type="secondary" className="assistant-starter-empty-text">
                              当前实验暂无视频点位，仍可在下方输入章节问题。
                            </Text>
                          )}
                        </section>

                        <section className="assistant-starter-column">
                          <div className="assistant-starter-section-title">3. 选择想问的方向</div>
                          <div className="assistant-starter-intents">
                            {learningAssistantPointIntents.map((intent) => (
                              <button
                                type="button"
                                key={intent.id}
                                className={`assistant-starter-intent ${starterIntent.id === intent.id ? "selected" : ""}`}
                                onClick={() => applyStarterIntent(intent)}
                                disabled={assistantStreaming || !starterPointContext}
                              >
                                <span>{intent.label}</span>
                                <small>{intent.description}</small>
                              </button>
                            ))}
                          </div>
                        </section>
                      </div>

                      <div className="assistant-starter-preview">
                        <div className="assistant-starter-preview-question">
                          {starterQuestion ? (
                            renderAssistantInlineMarkdown(starterQuestion)
                          ) : (
                            <Text type="secondary">已选择点位上下文，请在下方输入自己的问题。</Text>
                          )}
                        </div>
                        <div className="assistant-starter-launch-row">
                          <AIGlowButton
                            type="button"
                            className="assistant-starter-launch"
                            onClick={() => void submitStarterQuestion()}
                            disabled={starterLaunchDisabled}
                            glowColor="rgba(194, 255, 219, 0.44)"
                            glowSoftColor="rgba(73, 219, 132, 0.22)"
                            washColor="rgba(183, 255, 210, 0.5)"
                            washSoftColor="rgba(72, 211, 126, 0.24)"
                            background="linear-gradient(135deg, #00552c 0%, #04723c 48%, #139653 100%)"
                          >
                            <span className="assistant-launch-label">从这个问题开始</span>
                            <span className="assistant-launch-arrow">
                              <ArrowRightOutlined />
                            </span>
                          </AIGlowButton>
                        </div>
                      </div>
                    </>
                  ) : (
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description="当前章节暂无可用视频点位"
                    >
                      <Text type="secondary">仍可在下方输入框发送章节范围内的问题。</Text>
                    </Empty>
                  )}
                </div>
              )}
            </div>
            <div className="assistant-chat-composer">
              {activePointContext ? (
                <div className="assistant-active-point-context">
                  <div>
                    <Text type="secondary">当前点位</Text>
                    <div className="assistant-active-point-title">
                      {[activePointContext.experimentCode, activePointContext.experimentTitle]
                        .map((item) => String(item || "").trim())
                        .filter(Boolean)
                        .join(" · ") || activePointContext.experimentId || "-"}
                      {" / "}
                      点位 {activePointContext.pointIndex || "-"}
                    </div>
                    <Text type="secondary">
                      {activePointContext.pointTitle || activePointContext.pointKey || "-"}
                    </Text>
                  </div>
                  <Button
                    size="small"
                    onClick={() => setActivePointContext(null)}
                    disabled={assistantStreaming}
                  >
                    清除
                  </Button>
                </div>
              ) : null}
              <div className={`assistant-composer-box ${chatDraftAtLimit ? "assistant-composer-box-limit" : ""}`}>
                <Input.TextArea
                  className="assistant-chat-textarea"
                  value={chatDraft}
                  onChange={(event) => setChatDraft(event.target.value)}
                  onPressEnter={(event) => {
                    if (!event.shiftKey && !(event.nativeEvent as KeyboardEvent).isComposing) {
                      event.preventDefault();
                      void submit();
                    }
                  }}
                  autoSize={{ minRows: 1, maxRows: 8 }}
                  maxLength={chatDraftMaxLength}
                  placeholder="输入学生问题"
                  disabled={assistantStreaming}
                />
                <div className="assistant-composer-footer">
                  <span className={`assistant-composer-count ${chatDraftAtLimit ? "assistant-composer-count-limit" : ""}`}>
                    {chatDraftLength} / {chatDraftMaxLength}
                  </span>
                  <Button
                    type="primary"
                    icon={<ArrowRightOutlined />}
                    loading={assistantStreaming}
                    disabled={!chatDraft.trim() || assistantStreaming}
                    onClick={() => void submit()}
                  >
                    发送
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card
          title={selectedTurnIndex >= 0 ? `轮次诊断 · 第 ${selectedTurnIndex + 1} 轮` : "轮次诊断"}
          className="learning-assistant-card learning-assistant-inspector"
        >
          {selectedTurn && response ? (
            <Space orientation="vertical" size={14} className="full">
              <Space wrap>
                <Tag color="#005826">{policyLabel}</Tag>
                <Tooltip title={response.mode}>
                  <Tag>{modeLabel}</Tag>
                </Tooltip>
                {response.review_required ? <Tag color="#b8892f">记录留痕</Tag> : null}
              </Space>

              <div>
                <Text strong>护栏评估</Text>
                <div className="assistant-pill-list">
                  {response.guardrail_decisions.length ? response.guardrail_decisions.map((item, index) => {
                    const guardrailCode = String(item.code || "");
                    const guardrailAction = String(item.action || "");
                    return (
                      <Tooltip
                        key={`${guardrailCode || "guardrail"}-${index}`}
                        title={`${guardrailCode || "guardrail"} · ${guardrailAction || "-"}${item.reason ? `：${item.reason}` : ""}`}
                      >
                        <Tag color="#356f9c">
                          {learningAssistantGuardrailLabels[guardrailCode] || guardrailCode || "护栏"} · {learningAssistantActionLabels[guardrailAction] || guardrailAction || "-"}
                        </Tag>
                      </Tooltip>
                    );
                  }) : <Text type="secondary">无触发</Text>}
                </div>
              </div>

              <div>
                <Text strong>固定点位上下文</Text>
                {pointContextEnabled ? (
                  <>
                    <Descriptions column={1} size="small" className="assistant-rag-desc">
                      <Descriptions.Item label="实验">
                        {[
                          pointContextTrace.experiment_code,
                          pointContextTrace.experiment_title,
                        ].map((item) => String(item || "").trim()).filter(Boolean).join(" · ") || String(pointContextTrace.experiment_id || "-")}
                      </Descriptions.Item>
                      <Descriptions.Item label="点位">
                        <Tag color={pointContextTrace.resolved === false ? "orange" : "#005826"}>
                          {pointContextTrace.resolved === false ? "按传入点位保留" : "已解析"}
                        </Tag>
                        <Text>{String(pointContextTrace.point_title || pointContextTrace.point_key || "-")}</Text>
                      </Descriptions.Item>
                      <Descriptions.Item label="点位 key">
                        <Tag>{String(pointContextTrace.point_key || "-")}</Tag>
                        {pointContextTrace.requested_point_key && pointContextTrace.requested_point_key !== pointContextTrace.point_key ? (
                          <Tag color="blue">传入：{String(pointContextTrace.requested_point_key)}</Tag>
                        ) : null}
                      </Descriptions.Item>
                      <Descriptions.Item label="固定证据">
                        <Tag color={pointContextEvidenceSource === "manual_reviewed_point_evidence" ? "#005826" : "default"}>
                          {pointContextEvidenceSource === "manual_reviewed_point_evidence" ? "人工审核点位证据" : pointContextEvidenceSource || "未装载"}
                        </Tag>
                        <Tag color={pointContextTrace.manual_reviewed === true ? "#005826" : "default"}>
                          {pointContextTrace.manual_reviewed === true ? "manual reviewed" : "未确认人工审核"}
                        </Tag>
                        {pointContextReviewGrade ? <Tag color={pointContextReviewGrade === "weak_but_best_available" ? "orange" : "#005826"}>{pointContextReviewGrade}</Tag> : null}
                        <Tag color={pointContextSourceCount ? "#005826" : "default"}>来源 {pointContextSourceCount ?? 0}</Tag>
                        <Tag>实验证据 {pointContextExperimentSourceCount ?? pointContextExperimentChunkIds.length}</Tag>
                        <Tag>理论证据 {pointContextTheorySourceCount ?? pointContextTheoryChunkIds.length}</Tag>
                        {pointContextMissingChunkIds.length ? <Tag color="orange">缺失 chunk {pointContextMissingChunkIds.length}</Tag> : null}
                        {pointContextChunkIds.slice(0, 4).map((chunkId) => <Tag key={chunkId}>{chunkId}</Tag>)}
                      </Descriptions.Item>
                    </Descriptions>
                    {pointContextSources.length ? (
                      <div className="assistant-point-evidence-list">
                        {pointContextSources.slice(0, 3).map((source, index) => (
                          <div key={String(source.chunk_id || index)} className="assistant-point-evidence-item">
                            <Space size={8} wrap>
                              <Tag color="#005826">固定 #{index + 1}</Tag>
                              {source.evidence_kind ? <Tag>{String(source.evidence_kind)}</Tag> : null}
                              <Text strong>{String(source.caption || source.source_file || source.chunk_id || "点位证据")}</Text>
                              {source.page_number ? <Text type="secondary">p.{String(source.page_number)}</Text> : null}
                              {Array.isArray(source.assets) && source.assets.length ? <Tag color="blue">图像 {source.assets.length}</Tag> : null}
                            </Space>
                            <Text type="secondary" className="block-text">
                              {renderAssistantInlineMarkdown(String(source.text_preview || ""))}
                            </Text>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <Text type="secondary" className="block-text">
                        本轮保留了结构化点位，但未装载到人工审核点位固定来源片段。请确认 experiment_video_point_evidence 已导入且 source_chunks 引用有效。
                      </Text>
                    )}
                  </>
                ) : (
                  <Text type="secondary" className="block-text">本轮未携带结构化视频点位。</Text>
                )}
              </div>

              <div>
                <Text strong>补充 RAG 查询与重排</Text>
                <Descriptions column={1} size="small" className="assistant-rag-desc">
                  <Descriptions.Item label="模式">{String(latestRagTrace.mode || "-")}</Descriptions.Item>
                  <Descriptions.Item label="最终排序">
                    <Tag color={traceReranked ? "#005826" : "default"}>
                      {traceReranked ? "BGE reranker 已重排" : String(latestRagTrace.final_sort || "未使用重排")}
                    </Tag>
                    {traceReranked ? <Text type="secondary">来源证据按 final_evidence.rank 展示</Text> : null}
                  </Descriptions.Item>
                  <Descriptions.Item label="生成 Query">
                    {Array.isArray(latestRagTrace.generated_queries) && latestRagTrace.generated_queries.length
                      ? latestRagTrace.generated_queries.map((item) => <Tag key={String(item)}>{String(item)}</Tag>)
                      : <Text type="secondary">无</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="降级">
                    {Array.isArray(latestRagTrace.fallbacks) && latestRagTrace.fallbacks.length
                      ? latestRagTrace.fallbacks.map((item, index) => (
                        <Tag color="orange" key={`fallback-${index}`}>
                          {String((item as Record<string, unknown>).stage || "fallback")}
                        </Tag>
                      ))
                      : <Text type="secondary">无</Text>}
                  </Descriptions.Item>
                </Descriptions>
                <div className="assistant-trace-metrics">
                  <div>
                    <span>总耗时</span>
                    <strong>{formatTraceMs(traceTimings.total_ms)}</strong>
                  </div>
                  <div>
                    <span>Query 生成</span>
                    <strong>{formatTraceMs(traceTimings.query_generation_ms)}</strong>
                  </div>
                  <div>
                    <span>BGE Embedding</span>
                    <strong>{formatTraceMs(traceTimings.bge_embed_ms_total)}</strong>
                  </div>
                  <div>
                    <span>向量召回</span>
                    <strong>{formatTraceMs(traceTimings.vector_recall_ms_total)}</strong>
                  </div>
                  <div>
                    <span>BGE Rerank</span>
                    <strong>{formatTraceMs(traceTimings.bge_rerank_ms)}</strong>
                  </div>
                  <div>
                    <span>候选池</span>
                    <strong>
                      {mergedCount === undefined
                        ? "-"
                        : `${keywordTotalCount || 0} + ${vectorCount || 0} → ${mergedCount}`}
                    </strong>
                  </div>
                  <div>
                    <span>重排池</span>
                    <strong>{rerankPoolCount === undefined ? "-" : String(rerankPoolCount)}</strong>
                  </div>
                  <div>
                    <span>最终证据</span>
                    <strong>{finalEvidenceCount === undefined ? "-" : String(finalEvidenceCount)}</strong>
                  </div>
                </div>
              </div>

              <div>
                <Text strong>来源证据</Text>
                <div className="assistant-source-list">
                  {response.sources.length ? response.sources.map((source, index) => {
                    const evidence = findFinalEvidence(source, finalEvidence);
                    return (
                      <div key={source.chunk_id} className="assistant-source-item">
                        <div className="assistant-source-head">
                          <Space size={8} wrap>
                            <Tag color={traceReranked ? "#005826" : "default"}>
                              #{String(evidence?.rank || index + 1)}
                            </Tag>
                            <Text strong>{source.caption || source.source_file || source.chunk_id}</Text>
                          </Space>
                          {source.page_number ? <Text type="secondary">p.{source.page_number}</Text> : null}
                        </div>
                        <div className="assistant-source-tags">
                          <Tag>{sourceKindLabel(evidence?.source)}</Tag>
                          {source.content_type ? <Tag>{source.content_type === "figure" ? "图像 chunk" : source.content_type}</Tag> : null}
                          {evidence?.rerank_score !== undefined ? (
                            <Tag color="#005826">rerank {String(evidence.rerank_score)}</Tag>
                          ) : null}
                          {evidence?.score !== undefined ? <Tag>score {String(evidence.score)}</Tag> : null}
                          <Tag>{source.chunk_id}</Tag>
                        </div>
                        {source.section_path?.length ? (
                          <Text type="secondary" className="block-text">
                            章节：{source.section_path.join(" / ")}
                          </Text>
                        ) : null}
                        {evidence?.query ? (
                          <Text type="secondary" className="block-text">Query：{String(evidence.query)}</Text>
                        ) : null}
                        <Text type="secondary" className="block-text">
                          {renderAssistantInlineMarkdown(source.text_preview)}
                        </Text>
                        {source.assets?.length ? (
                          <div className="assistant-source-assets">
                            {source.assets.slice(0, 3).map((asset) => (
                              <RagAssetPreview asset={asset} key={`${source.chunk_id}-${asset.kind}-${asset.path}`} />
                            ))}
                          </div>
                        ) : null}
                      </div>
                    );
                  }) : <Text type="secondary" className="block-text">无来源</Text>}
                </div>
              </div>

              <div>
                <Text strong>分类与工具调用</Text>
                <pre className="assistant-json">
                  {JSON.stringify({
                    classification: response.classification,
                    tool_calls: response.tool_calls,
                    rag_trace: response.rag_trace,
                    guardrail_decisions: response.guardrail_decisions,
                  }, null, 2)}
                </pre>
              </div>
            </Space>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择一个助手轮次查看诊断" />
          )}
        </Card>
      </div>
    </Space>
  );
}
