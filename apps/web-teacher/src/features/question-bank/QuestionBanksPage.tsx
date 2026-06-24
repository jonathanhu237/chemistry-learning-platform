import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Tree,
  Typography,
} from "antd";
import type { DataNode } from "antd/es/tree";
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  FolderOutlined,
  MessageOutlined,
  ReloadOutlined,
} from "@ant-design/icons";

import type { ApiList } from "../../api/common";
import { api, patchJson, postJson, postJsonStream } from "../../api/http";
import type {
  CatalogQuestionBankNode,
  CatalogQuestionBankResponse,
  Question,
  QuestionDraft,
  SourceRef,
  QuestionWorkbenchCandidate,
  QuestionWorkbenchSession,
} from "../../api/questionBank";
import { listCatalogQuestionBank, refreshCatalogQuestionBankEvidence } from "../../api/questionBank";
import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { AssistantMarkdownContent } from "../../lib/assistant-markdown";
import { errorMessage } from "../../lib/errors";
import { formatChapterTitle } from "../../lib/resourceUtils";
import {
  answerText,
  candidatePayload,
  candidateQuestionPoints,
  candidateQuestionType,
  candidateStem,
  candidateValidationErrors,
  evidenceStatusTag,
  evidenceStatusText,
  questionBankStatusTag,
  questionBankStatusText,
  questionPointTitles,
  questionTypeLabel,
  questionWorkbenchGateFromRuntime,
  sourceRefLabel,
  textbookSectionLabels,
  workbenchEvidenceSectionsFromPackage,
} from "./questionBankDisplay";
import "./question-bank.css";

const { Text, Title } = Typography;

type TreeNodeWithTitle = DataNode & {
  title: ReactNode;
  children?: TreeNodeWithTitle[];
};

type ReviewItem =
  | { kind: "candidate"; key: string; candidate: QuestionWorkbenchCandidate; draft?: QuestionDraft | null }
  | { kind: "draft"; key: string; draft: QuestionDraft };

type DraftEditorState = {
  draftId: string;
  questionType: Question["question_type"];
  stem: string;
  optionsText: string;
  answerText: string;
  explanation: string;
  payload: Partial<Question> & Record<string, unknown>;
};

type DuplicateRiskMatch = {
  kind?: string;
  owner_kind?: string;
  owner_id?: string;
  question_type?: string;
  stem?: string;
  score?: number;
  reason?: string;
};

type DuplicateRisk = {
  has_risk?: boolean;
  message?: string;
  matches?: DuplicateRiskMatch[];
};

function nodePath(node?: CatalogQuestionBankNode | null) {
  return (node?.breadcrumb_titles || []).join(" / ");
}

function cleanText(value?: string | null) {
  return String(value || "").trim();
}

function cleanSourceText(value: unknown) {
  return String(value || "").trim();
}

function sourcePageLabel(source?: Record<string, unknown> | null) {
  if (!source) return "-";
  const start = cleanSourceText(source.page_start);
  const end = cleanSourceText(source.page_end);
  const page = cleanSourceText(source.page_number);
  if (start && end && start !== end) return `第 ${start}-${end} 页`;
  if (start || end) return `第 ${start || end} 页`;
  return page ? `第 ${page} 页` : "-";
}

function sourceSectionPathLabel(source?: Record<string, unknown> | null) {
  const path = source?.section_path;
  if (Array.isArray(path) && path.length) return path.map(String).filter(Boolean).join(" / ");
  return cleanSourceText(source?.section_title) || "-";
}

function sourceScoreLabel(value: unknown) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) return "-";
  return numberValue.toFixed(4);
}

function sourceEvidenceText(source?: Record<string, unknown> | null) {
  return cleanSourceText(source?.text) || cleanSourceText(source?.text_preview);
}

function sourceEvidenceMarkdown(source?: Record<string, unknown> | null) {
  return sourceEvidenceText(source)
    .replace(/^(#{1,6}\s+.*?)(\s+)(?=（\d+）|\(\d+\)|①|②|③|④|⑤|⑥)/u, "$1\n\n")
    .replace(/\s+(?=（\d+）|\(\d+\)|①|②|③|④|⑤|⑥)/g, "\n\n");
}

function principleText(node?: CatalogQuestionBankNode | null) {
  if (!node) return "";
  if (node.principle_mode === "equation") {
    return cleanText(node.principle_equation) || cleanText(node.principle_text);
  }
  return cleanText(node.principle_text) || cleanText(node.principle_equation);
}

function nodeEvidenceTone(node?: CatalogQuestionBankNode | null) {
  const status = node?.evidence_status || "missing";
  if (["available", "succeeded", "fresh"].includes(status)) return "green";
  if (["pending", "running", "stale"].includes(status)) return "gold";
  return "default";
}

function nodeEvidenceLabel(node?: CatalogQuestionBankNode | null) {
  const status = node?.evidence_status || "missing";
  const labels: Record<string, string> = {
    available: "证据可用",
    succeeded: "证据可用",
    fresh: "证据可用",
    pending: "证据待生成",
    running: "证据生成中",
    stale: "证据需刷新",
    missing: "证据缺失",
    failed: "证据失败",
  };
  return labels[status] || status;
}

function statusCountLine(node?: CatalogQuestionBankNode | null) {
  const counts = node?.counts;
  if (!counts) return "0 题";
  return `${counts.question_count || 0} 题 · 选 ${counts.choice_count || 0} · 判 ${counts.true_false_count || 0} · 填 ${counts.fill_blank_count || 0}`;
}

function buildQuestionBankTree(nodes: CatalogQuestionBankNode[]): TreeNodeWithTitle[] {
  const childrenByParent = new Map<string | null, CatalogQuestionBankNode[]>();
  nodes.forEach((node) => {
    const parent = node.parent_id || null;
    const current = childrenByParent.get(parent) || [];
    current.push(node);
    childrenByParent.set(parent, current);
  });
  const sortNodes = (items: CatalogQuestionBankNode[]) =>
    [...items].sort((a, b) => Number(a.display_order || 0) - Number(b.display_order || 0) || a.title.localeCompare(b.title, "zh-Hans-CN"));
  const toTreeNode = (node: CatalogQuestionBankNode): TreeNodeWithTitle => {
    const isPoint = node.node_kind === "point";
    const counts = node.counts || {};
    return {
      key: node.node_id,
      icon: isPoint ? <ExperimentOutlined /> : <FolderOutlined />,
      title: (
        <span className={`question-catalog-tree-title is-${node.node_kind}`}>
          <span className="question-catalog-tree-name">{node.title}</span>
          <span className="question-catalog-tree-count">
            {isPoint ? `${counts.question_count || 0} 题` : `${node.descendant_point_count || 0} 点`}
          </span>
        </span>
      ),
      selectable: true,
      children: sortNodes(childrenByParent.get(node.node_id) || []).map(toTreeNode),
    };
  };
  return sortNodes(childrenByParent.get(null) || []).map(toTreeNode);
}

function selectedPointNodes(nodes: CatalogQuestionBankNode[]) {
  return nodes.filter((node) => node.node_kind === "point");
}

function questionParams({
  selectedPoint,
  questionType,
  statusFilter,
  search,
}: {
  selectedPoint?: CatalogQuestionBankNode | null;
  questionType?: string;
  statusFilter?: string;
  search?: string;
}) {
  const params = new URLSearchParams({ limit: "1000" });
  if (selectedPoint?.node_id) params.set("point_node_id", selectedPoint.node_id);
  if (selectedPoint?.canonical_point_id) params.set("canonical_point_id", selectedPoint.canonical_point_id);
  if (questionType) params.set("question_type", questionType);
  if (statusFilter && statusFilter !== "all") params.set("status_filter", statusFilter);
  if (search?.trim()) params.set("search", search.trim());
  return params;
}

function draftParams(selectedPoint?: CatalogQuestionBankNode | null) {
  const params = new URLSearchParams();
  if (selectedPoint?.node_id) params.set("point_node_id", selectedPoint.node_id);
  if (selectedPoint?.canonical_point_id) params.set("canonical_point_id", selectedPoint.canonical_point_id);
  return params;
}

function draftPayload(draft: QuestionDraft) {
  return draft.payload || {};
}

function draftQuestionType(draft: QuestionDraft) {
  return String(draftPayload(draft).question_type || "");
}

function draftStem(draft: QuestionDraft) {
  return String(draftPayload(draft).stem || "");
}

function draftValidationErrors(draft: QuestionDraft) {
  return draft.validation_errors || [];
}

function duplicateRiskFromPayload(payload: Partial<Question> & Record<string, unknown>): DuplicateRisk | null {
  const metadata = payload.metadata && typeof payload.metadata === "object" ? (payload.metadata as Record<string, unknown>) : {};
  const risk = metadata.duplicate_risk && typeof metadata.duplicate_risk === "object" ? (metadata.duplicate_risk as DuplicateRisk) : null;
  return risk?.has_risk ? risk : null;
}

function duplicateRiskMatches(risk: DuplicateRisk | null) {
  return Array.isArray(risk?.matches) ? risk.matches.filter((match) => match && typeof match === "object") : [];
}

function duplicateRiskMessage(risk: DuplicateRisk | null) {
  const matches = duplicateRiskMatches(risk);
  return risk?.message || `这道题可能与 ${matches.length || 1} 道同点位题目考察意图相近，请发布前确认。`;
}

function duplicateRiskKindLabel(match: DuplicateRiskMatch) {
  return match.kind === "draft" || match.owner_kind === "draft" ? "待审" : "已发布";
}

function normalizeQuestionType(value: unknown): Question["question_type"] {
  if (value === "single_choice" || value === "true_false" || value === "fill_blank") return value;
  return "single_choice";
}

function optionsToText(options: unknown) {
  if (!Array.isArray(options)) return "";
  return options
    .map((option, index) => {
      const fallbackLabel = String.fromCharCode(65 + index);
      if (typeof option === "string") return `${fallbackLabel}. ${option}`;
      const item = option as Record<string, unknown>;
      return `${cleanText(String(item.label || fallbackLabel))}. ${cleanText(String(item.text || ""))}`.trim();
    })
    .filter(Boolean)
    .join("\n");
}

function textToOptions(value: string) {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const match = line.match(/^([A-Za-z])[\s.、)、:：-]+(.+)$/);
      if (match) return { label: match[1].toUpperCase(), text: match[2].trim() };
      return { label: String.fromCharCode(65 + index), text: line };
    });
}

function answerToEditableText(questionType: Question["question_type"], answer: unknown) {
  const answerValue = answer as Record<string, unknown>;
  if (questionType === "fill_blank") {
    const accepted = Array.isArray(answerValue?.accepted_answers) ? answerValue.accepted_answers : [];
    return accepted.length ? accepted.map(String).join("；") : cleanText(String(answer || ""));
  }
  const value = answerValue && typeof answerValue === "object" && "value" in answerValue ? answerValue.value : answer;
  if (questionType === "true_false") {
    if (value === true) return "正确";
    if (value === false) return "错误";
  }
  return cleanText(String(value ?? ""));
}

function editableAnswerToPayload(questionType: Question["question_type"], value: string) {
  const text = value.trim();
  if (questionType === "fill_blank") {
    return {
      accepted_answers: text
        .split(/[;；,\n，]/)
        .map((item) => item.trim())
        .filter(Boolean),
      match: "normalized_exact",
    };
  }
  return { value: text };
}

export function QuestionBanksPage() {
  const { message, modal } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [chapterId, setChapterId] = useState<string>("CH13");
  const [selectedNodeId, setSelectedNodeId] = useState<string>();
  const [questionType, setQuestionType] = useState<string>();
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [aiWorkbenchSessionId, setAiWorkbenchSessionId] = useState<string>();
  const [workbenchPrompt, setWorkbenchPrompt] = useState("");
  const [workbenchQuestionTypes, setWorkbenchQuestionTypes] = useState<Question["question_type"][]>([
    "single_choice",
    "true_false",
    "fill_blank",
  ]);
  const [workbenchCount, setWorkbenchCount] = useState(3);
  const [workbenchStreaming, setWorkbenchStreaming] = useState(false);
  const [workbenchStreamStatus, setWorkbenchStreamStatus] = useState("");
  const [selectedEvidenceSource, setSelectedEvidenceSource] = useState<SourceRef | null>(null);
  const [draftEditor, setDraftEditor] = useState<DraftEditorState | null>(null);
  const autoEvidencePointRef = useRef<string | undefined>(undefined);

  const catalog = useQuery<CatalogQuestionBankResponse>({
    queryKey: ["question-bank-catalog", chapterId],
    queryFn: () => listCatalogQuestionBank(chapterId),
  });
  const nodes = catalog.data?.items || [];
  const points = useMemo(() => selectedPointNodes(nodes), [nodes]);

  useEffect(() => {
    const current = nodes.find((node) => node.node_id === selectedNodeId);
    if (current?.node_kind === "point") return;
    setSelectedNodeId(points[0]?.node_id);
  }, [nodes, points, selectedNodeId]);

  const selectedPoint = useMemo(
    () => nodes.find((node) => node.node_id === selectedNodeId && node.node_kind === "point") || null,
    [nodes, selectedNodeId],
  );

  useEffect(() => {
    setAiWorkbenchSessionId(undefined);
    setSelectedEvidenceSource(null);
    setWorkbenchStreamStatus("");
    setWorkbenchStreaming(false);
    setWorkbenchQuestionTypes(["single_choice", "true_false", "fill_blank"]);
    setWorkbenchCount(3);
    setWorkbenchPrompt(
      selectedPoint
        ? `请围绕「${selectedPoint.title}」生成一组可机判的实验题，覆盖实验原理、现象解释和安全提示。`
        : "",
    );
  }, [selectedPoint?.node_id]);
  const selectedChapter = catalog.data?.chapters.find((chapter) => chapter.chapter_id === chapterId);
  const treeData = useMemo(() => buildQuestionBankTree(nodes), [nodes]);
  const expandedRootKeys = useMemo(
    () => nodes.filter((node) => !node.parent_id && node.node_kind === "directory").map((node) => node.node_id),
    [nodes],
  );

  const params = useMemo(
    () => questionParams({ selectedPoint, questionType, statusFilter, search }),
    [questionType, search, selectedPoint, statusFilter],
  );
  const questions = useQuery({
    queryKey: ["question-bank-catalog-questions", params.toString()],
    queryFn: () => api<ApiList<Question>>(`/api/admin/question-banks/questions?${params.toString()}`),
    enabled: Boolean(selectedPoint),
  });
  const draftsQueryParams = useMemo(() => draftParams(selectedPoint), [selectedPoint]);
  const drafts = useQuery({
    queryKey: ["question-bank-catalog-drafts", draftsQueryParams.toString()],
    queryFn: () => api<ApiList<QuestionDraft>>(`/api/admin/question-banks/drafts?${draftsQueryParams.toString()}`),
    enabled: Boolean(selectedPoint),
  });
  const assistantRuntime = useQuery({
    queryKey: ["learning-assistant-runtime", "question-bank-workbench"],
    queryFn: () => api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime"),
    refetchInterval: 10000,
  });
  const aiWorkbench = useQuery({
    queryKey: ["question-ai-workbench", aiWorkbenchSessionId],
    queryFn: () => api<QuestionWorkbenchSession>(`/api/admin/question-banks/workbench-sessions/${aiWorkbenchSessionId}`),
    enabled: Boolean(aiWorkbenchSessionId),
  });

  const workbenchContext = aiWorkbench.data?.context_snapshot || {};
  const workbenchCandidates = aiWorkbench.data?.candidates || [];
  const workbenchTurns = aiWorkbench.data?.turns || [];
  const workbenchEvidencePackage = workbenchContext.evidence_package;
  const workbenchEvidenceSections = workbenchEvidenceSectionsFromPackage(workbenchEvidencePackage);
  const questionWorkbenchGate = questionWorkbenchGateFromRuntime(assistantRuntime.data);
  const workbenchRagGate = workbenchContext.rag_gate;
  const workbenchStatusTone = workbenchRagGate?.healthy === false ? "blocked" : questionWorkbenchGate.tone;
  const workbenchEvidenceSourceCount = workbenchEvidencePackage?.source_count ?? (workbenchContext.source_refs || []).length;
  const workbenchEvidenceStatusText = `已读取 ${workbenchEvidenceSourceCount || 0} 条已绑定教材证据`;
  const selectedEvidenceReady = Boolean(
    selectedPoint && ["succeeded", "partial", "fresh", "available"].includes(selectedPoint.evidence_status || ""),
  );
  const evidenceBlockedText = selectedPoint ? `${nodeEvidenceLabel(selectedPoint)}，请先刷新教材证据。` : "请先选择一个点位";
  const canGenerateWithAI = Boolean(
    selectedPoint &&
      questionWorkbenchGate.healthy &&
      selectedEvidenceReady &&
      workbenchPrompt.trim() &&
      workbenchQuestionTypes.length &&
      !workbenchStreaming,
  );

  const refreshQuestionBank = () => {
    void queryClient.invalidateQueries({ queryKey: ["question-bank-catalog"] });
    void queryClient.invalidateQueries({ queryKey: ["question-bank-catalog-questions"] });
    void queryClient.invalidateQueries({ queryKey: ["question-bank-catalog-drafts"] });
  };

  const refreshEvidence = useMutation({
    mutationFn: (payload: {
      chapter_id?: string | null;
      point_node_id?: string | null;
      force?: boolean;
      process_now?: boolean;
      process_limit?: number;
    }) => refreshCatalogQuestionBankEvidence(payload),
    onSuccess: (result) => {
      message.success(
        result.queued_count
          ? `已开始刷新 ${result.queued_count} 个点位证据，预估 ${result.qwen_call_estimate} 次 Qwen 调用`
          : `没有新点位需要刷新，已跳过 ${result.skipped_count} 个点位`,
      );
      refreshQuestionBank();
      window.setTimeout(refreshQuestionBank, 2500);
      window.setTimeout(refreshQuestionBank, 8000);
    },
    onError: (error) => message.error(`证据刷新失败：${errorMessage(error)}`),
  });

  const startWorkbench = useMutation({
    mutationFn: (payload: {
      mode: "create";
      experiment_id: string;
      point_node_id: string;
      point_node_ids: string[];
      point_key?: string | null;
    }) => postJson<QuestionWorkbenchSession>("/api/admin/question-banks/workbench-sessions", payload),
    onSuccess: (result) => {
      setAiWorkbenchSessionId(result.id);
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", result.id] });
    },
    onError: (error) => message.error(`AI 出题准备失败：${errorMessage(error)}`),
  });

  const publishCandidate = useMutation({
    mutationFn: (candidateId: string) => postJson<Question>(`/api/admin/question-banks/workbench-candidates/${candidateId}/publish`, {}),
    onSuccess: () => {
      message.success("待审题目已发布");
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      refreshQuestionBank();
    },
    onError: (error) => message.error(`发布失败：${errorMessage(error)}`),
  });

  const rejectCandidate = useMutation({
    mutationFn: (candidateId: string) => postJson<QuestionWorkbenchCandidate>(`/api/admin/question-banks/workbench-candidates/${candidateId}/reject`, {}),
    onSuccess: () => {
      message.success("待审题目已拒绝");
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      refreshQuestionBank();
    },
    onError: (error) => message.error(`拒绝失败：${errorMessage(error)}`),
  });

  const publishDraft = useMutation({
    mutationFn: (draftId: string) => postJson<Question>(`/api/admin/question-banks/drafts/${draftId}/publish`, {}),
    onSuccess: () => {
      message.success("待审题目已发布");
      refreshQuestionBank();
    },
    onError: (error) => message.error(`待审题目发布失败：${errorMessage(error)}`),
  });

  const rejectDraft = useMutation({
    mutationFn: (draftId: string) => postJson<QuestionDraft>(`/api/admin/question-banks/drafts/${draftId}/reject`, {}),
    onSuccess: () => {
      message.success("待审题目已拒绝");
      refreshQuestionBank();
    },
    onError: (error) => message.error(`待审题目拒绝失败：${errorMessage(error)}`),
  });

  const updateDraft = useMutation({
    mutationFn: ({ draftId, payload }: { draftId: string; payload: Partial<Question> & Record<string, unknown> }) =>
      patchJson<QuestionDraft>(`/api/admin/question-banks/drafts/${draftId}`, { payload, status: "draft" }),
    onSuccess: () => {
      message.success("待审题目已保存");
      setDraftEditor(null);
      if (aiWorkbenchSessionId) {
        void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      }
      refreshQuestionBank();
    },
    onError: (error) => message.error(`保存失败：${errorMessage(error)}`),
  });

  const openQuestionDetail = (question: Question) => {
    setSelectedQuestion(question);
    setDetailOpen(true);
  };

  const openDraftEditor = (item: ReviewItem) => {
    const draftId = item.kind === "candidate" ? item.candidate.draft_id : item.draft.id;
    if (!draftId) {
      message.warning("这条待审题目缺少草稿记录，暂时不能手动编辑");
      return;
    }
    const payload = item.kind === "candidate" && item.draft ? draftPayload(item.draft) : item.kind === "candidate" ? candidatePayload(item.candidate) : draftPayload(item.draft);
    const questionType = normalizeQuestionType(payload.question_type);
    setDraftEditor({
      draftId,
      questionType,
      stem: cleanText(String(payload.stem || "")),
      optionsText: optionsToText(payload.options),
      answerText: answerToEditableText(questionType, payload.answer),
      explanation: cleanText(String(payload.explanation || "")),
      payload,
    });
  };

  const saveDraftEditor = () => {
    if (!draftEditor) return;
    const payload = {
      ...draftEditor.payload,
      question_type: draftEditor.questionType,
      stem: draftEditor.stem.trim(),
      options: draftEditor.questionType === "single_choice" ? textToOptions(draftEditor.optionsText) : [],
      answer: editableAnswerToPayload(draftEditor.questionType, draftEditor.answerText),
      explanation: draftEditor.explanation.trim(),
      status: "draft",
    };
    updateDraft.mutate({ draftId: draftEditor.draftId, payload });
  };

  const createWorkbenchSession = async () => {
    if (!selectedPoint) {
      message.warning("请先选择一个点位");
      return undefined;
    }
    if (!questionWorkbenchGate.healthy) {
      message.warning(questionWorkbenchGate.message);
      return undefined;
    }
    if (!selectedEvidenceReady) {
      message.warning(evidenceBlockedText);
      return undefined;
    }
    const result = await startWorkbench.mutateAsync({
      mode: "create",
      experiment_id: selectedPoint.experiment_id,
      point_node_id: selectedPoint.node_id,
      point_node_ids: [selectedPoint.node_id],
      point_key: selectedPoint.node_id,
    });
    return result.id;
  };

  const prepareWorkbenchSession = () => {
    void createWorkbenchSession();
  };

  useEffect(() => {
    if (!selectedPoint || aiWorkbenchSessionId || !questionWorkbenchGate.healthy || !selectedEvidenceReady || startWorkbench.isPending) {
      return;
    }
    if (autoEvidencePointRef.current === selectedPoint.node_id) return;
    autoEvidencePointRef.current = selectedPoint.node_id;
    void createWorkbenchSession();
  }, [
    aiWorkbenchSessionId,
    questionWorkbenchGate.healthy,
    selectedEvidenceReady,
    selectedPoint?.node_id,
    startWorkbench.isPending,
  ]);

  const sendWorkbenchMessage = async () => {
    if (!workbenchPrompt.trim() || workbenchStreaming) return;
    if (!questionWorkbenchGate.healthy) {
      message.warning(questionWorkbenchGate.message);
      return;
    }
    if (!workbenchQuestionTypes.length) {
      message.warning("请至少选择一种题型");
      return;
    }
    if (!selectedEvidenceReady) {
      message.warning(evidenceBlockedText);
      return;
    }
    const prompt = workbenchPrompt.trim();
    setWorkbenchStreaming(true);
    setWorkbenchStreamStatus("已发送提示，正在准备教材证据");
    try {
      const sessionId = aiWorkbenchSessionId || (await createWorkbenchSession());
      if (!sessionId) return;
      await postJsonStream<{ message?: string; session?: QuestionWorkbenchSession }>(
        `/api/admin/question-banks/workbench-sessions/${sessionId}/messages/stream`,
        {
          prompt,
          question_types: workbenchQuestionTypes,
          count: workbenchCount,
          difficulty: "basic",
        },
        ({ event, data }) => {
          if (event === "status") {
            setWorkbenchStreamStatus(String(data.message || "AI 正在生成待审题目"));
          }
          if (event === "final" && data.session) {
            queryClient.setQueryData(["question-ai-workbench", sessionId], data.session);
            message.success("AI 待审题目已更新");
            setWorkbenchPrompt("");
            void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", sessionId] });
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

  const confirmRefreshEvidence = (scope: "chapter" | "point", force = false) => {
    if (scope === "point" && !selectedPoint) {
      message.warning("请先选择一个点位");
      return;
    }
    modal.confirm({
      title: scope === "chapter" ? "刷新本章教材证据？" : "刷新当前点位教材证据？",
      content:
        scope === "chapter"
          ? "系统会为本章缺失、失败或过期的点位调用 Qwen Embedding 与 Rerank，并把命中的教材 chunk 绑定到点位。已有可用证据默认不会重复付费检索。"
          : "系统会调用 Qwen Embedding 与 Rerank，为当前点位的实验原理、现象解释和安全提示绑定教材依据。",
      okText: "开始刷新",
      cancelText: "取消",
      onOk: () =>
        refreshEvidence.mutate({
          chapter_id: scope === "chapter" ? chapterId : undefined,
          point_node_id: scope === "point" ? selectedPoint?.node_id : undefined,
          force,
          process_now: true,
          process_limit: scope === "chapter" ? 200 : 1,
        }),
    });
  };

  const totals = catalog.data?.totals;
  const selectedCounts = selectedPoint?.counts;
  const visibleQuestions = questions.data?.items || [];
  const visibleDrafts = drafts.data?.items || [];
  const reviewItems = useMemo<ReviewItem[]>(() => {
    const draftsById = new Map(visibleDrafts.map((draft) => [draft.id, draft]));
    const pendingCandidates = workbenchCandidates.filter(
      (candidate) =>
        candidate.status === "draft" &&
        (!candidate.draft_id || draftsById.get(candidate.draft_id)?.status === "draft" || candidate.draft_status === "draft"),
    );
    const candidateDraftIds = new Set(pendingCandidates.map((candidate) => candidate.draft_id).filter(Boolean));
    return [
      ...pendingCandidates.map((candidate) => ({
        kind: "candidate" as const,
        key: `candidate-${candidate.id}`,
        candidate,
        draft: candidate.draft_id ? draftsById.get(candidate.draft_id) || null : null,
      })),
      ...visibleDrafts
        .filter((draft) => draft.status === "draft" && !candidateDraftIds.has(draft.id))
        .map((draft) => ({
          kind: "draft" as const,
          key: `draft-${draft.id}`,
          draft,
        })),
    ];
  }, [visibleDrafts, workbenchCandidates]);

  return (
    <Space orientation="vertical" size={18} className="full question-bank-catalog-page">
      <PageTitle
        title="题库管理"
        description="按章节目录和主点位管理题目。题目只归属一个点位，AI 出题会先读取该点位三段式内容并检索教材证据。"
      />

      <div className="stat-grid question-bank-stat-grid">
        <Card>
          <Statistic title="目录点位" value={totals?.point_count || 0} suffix="个" prefix={<ExperimentOutlined />} />
        </Card>
        <Card>
          <Statistic title="当前题库" value={totals?.question_count || 0} suffix="题" prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="已发布" value={totals?.published_count || 0} suffix="题" prefix={<CheckCircleOutlined />} />
        </Card>
        <Card>
          <Statistic title="待审题目" value={totals?.draft_candidate_count || 0} suffix="题" prefix={<FileTextOutlined />} />
        </Card>
        <Card>
          <Statistic title="待覆盖" value={Math.max(0, (totals?.point_count || 0) - (totals?.published_count || 0))} suffix="点" />
        </Card>
      </div>

      <div className="question-bank-catalog-layout">
        <Card
          className="question-catalog-panel"
          title="章节目录与点位"
          extra={
            <Space size={6}>
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={refreshEvidence.isPending}
                disabled={!chapterId || refreshEvidence.isPending}
                onClick={() => confirmRefreshEvidence("chapter")}
              >
                刷新本章证据
              </Button>
              <Tag color="green">{points.length} 个点位</Tag>
            </Space>
          }
        >
          <Space orientation="vertical" size={12} className="full">
            <Select
              value={chapterId}
              onChange={(value) => {
                setChapterId(value);
                setSelectedNodeId(undefined);
                setQuestionType(undefined);
                setSearch("");
              }}
              options={(catalog.data?.chapters || []).map((chapter) => ({
                value: chapter.chapter_id,
                label: formatChapterTitle(chapter.chapter_title, chapter.chapter_id),
              }))}
              className="full"
              loading={catalog.isLoading}
            />
            <div className="question-catalog-chapter-line">
              <Text strong>{selectedChapter ? formatChapterTitle(selectedChapter.chapter_title, selectedChapter.chapter_id) : chapterId}</Text>
              <Text type="secondary">目录 {totals?.directory_count || 0} · 点位 {totals?.point_count || 0}</Text>
            </div>
            <QueryState loading={catalog.isLoading} error={catalog.error} empty={!treeData.length}>
              <Tree
                key={chapterId}
                showIcon
                blockNode
                defaultExpandedKeys={expandedRootKeys}
                selectedKeys={selectedNodeId ? [selectedNodeId] : []}
                treeData={treeData}
                onSelect={(keys) => {
                  const key = String(keys[0] || "");
                  const nextNode = nodes.find((node) => node.node_id === key);
                  if (nextNode?.node_kind === "point") {
                    setSelectedNodeId(key);
                    setSelectedQuestion(null);
                    setQuestionType(undefined);
                    setSearch("");
                  }
                }}
              />
            </QueryState>
          </Space>
        </Card>

        <div className="question-point-workspace">
          <Card className="question-point-header-card">
            {selectedPoint ? (
              <Flex justify="space-between" gap={16} wrap="wrap" align="start">
                <div className="question-point-heading">
                  <Text type="secondary">{nodePath(selectedPoint)}</Text>
                  <Title level={3}>{selectedPoint.title}</Title>
                  <Space size={6} wrap>
                    <Tag color={selectedPoint.content_status === "published" ? "green" : "default"}>
                      内容{selectedPoint.content_status === "published" ? "已发布" : selectedPoint.content_status || "未发布"}
                    </Tag>
                    <Tag color={nodeEvidenceTone(selectedPoint)}>{nodeEvidenceLabel(selectedPoint)}</Tag>
                    <Tag>{statusCountLine(selectedPoint)}</Tag>
                    <Tag>待审 {selectedCounts?.draft_candidate_count || 0}</Tag>
                  </Space>
                </div>
                <Space wrap>
                  <Button
                    icon={<ReloadOutlined />}
                    loading={refreshEvidence.isPending}
                    disabled={refreshEvidence.isPending}
                    onClick={() => confirmRefreshEvidence("point", selectedEvidenceReady)}
                  >
                    刷新当前点位证据
                  </Button>
                </Space>
              </Flex>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择一个点位" />
            )}
          </Card>

          {selectedPoint ? (
            <>
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
                </div>
              </div>

              <div className="question-authoring-shell">
                <Card
                  className="question-authoring-card question-authoring-evidence-card"
                  title="出题依据"
                  extra={<Tag color={selectedEvidenceReady ? "green" : "orange"}>{nodeEvidenceLabel(selectedPoint)}</Tag>}
                >
                  <Space orientation="vertical" size={14} className="full">
                    <div className={`question-workbench-status question-workbench-status-${workbenchStatusTone}`}>
                      <div className="question-workbench-status-main">
                        <span className="question-workbench-status-icon">
                          {workbenchStatusTone === "ready" ? <CheckCircleOutlined /> : workbenchStatusTone === "checking" ? <ReloadOutlined /> : <CloseCircleOutlined />}
                        </span>
                        <div className="question-workbench-status-copy">
                          <Text strong>{workbenchRagGate?.healthy === false ? "证据未生成" : "教材证据详情"}</Text>
                          <Text type="secondary">
                            {aiWorkbenchSessionId
                              ? workbenchRagGate?.healthy === false
                                ? String(workbenchRagGate.message || questionWorkbenchGate.message)
                                : workbenchEvidenceStatusText
                              : selectedEvidenceReady
                                ? "当前点位已有缓存证据，生成前会读取并展示。"
                                : evidenceBlockedText}
                          </Text>
                        </div>
                      </div>
                      <div className="question-workbench-status-meta">
                        <span>{questionWorkbenchGate.route}</span>
                      </div>
                    </div>

                    <div className="question-authoring-evidence-section">
                      <Flex justify="space-between" align="center" gap={10}>
                        <div>
                          <Text strong>教材证据详情</Text>
                          <Text type="secondary" className="question-authoring-subtext">
                            生成题目前会读取当前点位绑定的教材 chunk，点击来源可查看原文。
                          </Text>
                        </div>
                        {aiWorkbenchSessionId ? <Tag color="green">{workbenchEvidenceSourceCount || 0} 条证据</Tag> : null}
                      </Flex>
                      {aiWorkbenchSessionId ? (
                        <QueryState loading={aiWorkbench.isLoading || startWorkbench.isPending} error={aiWorkbench.error} empty={!workbenchEvidenceSections.length}>
                          <Space orientation="vertical" size={8} className="full">
                            {workbenchEvidenceSections.map((item) => (
                              <div key={`${item.pointKey}-${item.section}`} className="question-evidence-row">
                                <Text type="secondary">
                                  {item.pointTitle} · {textbookSectionLabels[item.section] || item.section}
                                </Text>
                                <div className="question-evidence-values">
                                  <Tag color={item.sufficient ? "green" : "orange"}>
                                    {item.sufficient ? `${item.sourceCount} 条证据` : item.missingReason || "证据不足"}
                                  </Tag>
                                  {item.sources.slice(0, 3).map((source: Record<string, unknown>, index: number) => (
                                    <button
                                      key={`${source.chunk_id || index}`}
                                      type="button"
                                      className="question-evidence-source-button"
                                      onClick={() => setSelectedEvidenceSource(source as SourceRef)}
                                      title="查看教材证据原文"
                                    >
                                      原文 · {sourceRefLabel(source)}
                                    </button>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </Space>
                        </QueryState>
                      ) : (
                        <Alert
                          type={selectedEvidenceReady ? "info" : "warning"}
                          showIcon
                          message={selectedEvidenceReady ? "证据尚未读取到页面" : "当前点位还不能出题"}
                          description={selectedEvidenceReady ? "可以先读取证据核对原文，也可以直接生成待审题目。" : evidenceBlockedText}
                          action={
                            selectedEvidenceReady ? (
                              <Button size="small" loading={startWorkbench.isPending} onClick={prepareWorkbenchSession}>
                                读取证据
                              </Button>
                            ) : null
                          }
                        />
                      )}
                    </div>

                    <div className="question-authoring-source-grid">
                      <section>
                        <Text strong>实验原理</Text>
                        <Text className="block-text">{principleText(selectedPoint) || "暂无实验原理"}</Text>
                      </section>
                      <section>
                        <Text strong>现象解释</Text>
                        <Text className="block-text">{cleanText(selectedPoint.phenomenon_explanation) || "暂无现象解释"}</Text>
                      </section>
                      <section>
                        <Text strong>安全提示</Text>
                        <Text className="block-text">{cleanText(selectedPoint.safety_note) || "暂无安全提示"}</Text>
                      </section>
                    </div>
                  </Space>
                </Card>

                <Card
                  id="question-ai-authoring"
                  className="question-authoring-card question-authoring-generate-card"
                  title="AI 生成与审核"
                  extra={
                    <Space size={6} wrap>
                      {workbenchStreaming && workbenchStreamStatus ? <Tag color="processing">{workbenchStreamStatus}</Tag> : null}
                      <Tag>{reviewItems.length} 条待审</Tag>
                    </Space>
                  }
                >
                  <Space orientation="vertical" size={14} className="full">
                    <div className="question-authoring-composer">
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
                          disabled={workbenchStreaming || !questionWorkbenchGate.healthy}
                          className="ai-workbench-type-select"
                        />
                        <InputNumber
                          min={1}
                          max={20}
                          value={workbenchCount}
                          onChange={(value) => setWorkbenchCount(Number(value || 1))}
                          addonBefore="数量"
                          disabled={workbenchStreaming || !questionWorkbenchGate.healthy}
                        />
                      </Space>
                      <Input.TextArea
                        rows={4}
                        value={workbenchPrompt}
                        disabled={workbenchStreaming || !questionWorkbenchGate.healthy}
                        onChange={(event) => setWorkbenchPrompt(event.target.value)}
                        placeholder="例如：生成 1 道选择题、1 道判断题、1 道填空题；题目必须能从教材证据直接推出答案。"
                      />
                      <Flex justify="space-between" align="center" gap={10} wrap="wrap">
                        <Text type="secondary">
                          {selectedEvidenceReady ? "生成结果会进入待审题目，发布后才进入题库。" : evidenceBlockedText}
                        </Text>
                        <Button
                          type="primary"
                          icon={<MessageOutlined />}
                          loading={workbenchStreaming || startWorkbench.isPending}
                          disabled={!canGenerateWithAI || startWorkbench.isPending}
                          onClick={sendWorkbenchMessage}
                        >
                          生成待审题目
                        </Button>
                      </Flex>
                    </div>

                    {workbenchStreaming ? (
                      <Alert type="info" showIcon message="正在生成待审题目" description={workbenchStreamStatus || "AI 正在读取证据并生成题目。"} />
                    ) : null}

                    <div className="question-authoring-candidate-block">
                      <Flex justify="space-between" align="center" gap={10}>
                        <Text strong>待审题目</Text>
                        <Text type="secondary">本次生成和历史待审统一在这里审核</Text>
                      </Flex>
                      <div className="ai-workbench-candidate-list">
                        <QueryState
                          loading={drafts.isLoading || (Boolean(aiWorkbenchSessionId) && aiWorkbench.isLoading)}
                          error={drafts.error || aiWorkbench.error}
                          empty={false}
                        >
                          {reviewItems.length ? (
                            reviewItems.map((item) => {
                              const isCandidate = item.kind === "candidate";
                              const draft = isCandidate ? item.draft : item.draft;
                              const draftId = isCandidate ? item.candidate.draft_id : item.draft.id;
                              const candidateId = isCandidate ? item.candidate.id : "";
                              const payload = draft ? draftPayload(draft) : isCandidate ? candidatePayload(item.candidate) : draftPayload(item.draft);
                              const errors = draft ? draftValidationErrors(draft) : isCandidate ? candidateValidationErrors(item.candidate) : draftValidationErrors(item.draft);
                              const status = draft ? draft.status : isCandidate ? item.candidate.status : item.draft.status;
                              const itemId = isCandidate ? item.candidate.id : item.draft.id;
                              const duplicateRisk = duplicateRiskFromPayload(payload);
                              const duplicateMatches = duplicateRiskMatches(duplicateRisk);
                              const questionType = normalizeQuestionType(payload.question_type);
                              const stem = cleanText(String(payload.stem || ""));
                              const pointTags = isCandidate
                                ? draft
                                  ? selectedPoint
                                    ? [
                                        {
                                          point_node_id: selectedPoint.node_id,
                                          point_key: selectedPoint.node_id,
                                          point_title: selectedPoint.title,
                                        },
                                      ]
                                    : []
                                  : candidateQuestionPoints(item.candidate).slice(0, 3)
                                : selectedPoint
                                  ? [
                                      {
                                        point_node_id: selectedPoint.node_id,
                                        point_key: selectedPoint.node_id,
                                        point_title: selectedPoint.title,
                                      },
                                    ]
                                  : [];
                              return (
                                <div key={item.key} className="ai-candidate-card">
                                  <Space orientation="vertical" size={8} className="full">
                                    <Flex justify="space-between" align="start" gap={8}>
                                      <Space size={4} wrap>
                                        <Tag color="blue">{questionTypeLabel(questionType)}</Tag>
                                        <Tag color={isCandidate ? "green" : "default"}>{isCandidate ? "本次生成" : "历史待审"}</Tag>
                                        {errors.length ? <Tag color="red">需修订</Tag> : <Tag color="green">可发布</Tag>}
                                        {duplicateRisk ? <Tag color="orange">疑似重复 · {duplicateMatches.length || 1} 条</Tag> : null}
                                        {status !== "draft" ? <Tag>{status}</Tag> : null}
                                      </Space>
                                      <Text type="secondary">{itemId.slice(0, 8)}</Text>
                                    </Flex>
                                    <Text strong>{stem || "未生成题干"}</Text>
                                    {Array.isArray(payload.options) && payload.options.length ? (
                                      <div className="question-options">
                                        {payload.options.map((option, index) => {
                                          const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
                                          const text = typeof option === "string" ? option : option.text || "";
                                          return (
                                            <div key={`${item.key}-${label}-${index}`} className="question-option">
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
                                    {duplicateRisk ? (
                                      <Alert
                                        type="warning"
                                        showIcon
                                        className="question-duplicate-risk"
                                        message={duplicateRiskMessage(duplicateRisk)}
                                        description={
                                          duplicateMatches.length ? (
                                            <div className="question-duplicate-risk-list">
                                              {duplicateMatches.map((match, matchIndex) => (
                                                <div key={`${item.key}-duplicate-${match.owner_id || matchIndex}`} className="question-duplicate-risk-item">
                                                  <Tag color={match.kind === "draft" || match.owner_kind === "draft" ? "gold" : "default"}>
                                                    {duplicateRiskKindLabel(match)}
                                                  </Tag>
                                                  <Text className="question-duplicate-risk-stem">{match.stem || "相似题目"}</Text>
                                                  {match.reason ? <Text type="secondary">{match.reason}</Text> : null}
                                                </div>
                                              ))}
                                            </div>
                                          ) : undefined
                                        }
                                      />
                                    ) : null}
                                    <Space size={4} wrap>
                                      {pointTags.map((point) => (
                                        <Tag key={point.point_node_id || point.point_key || point.point_title} color="cyan">
                                          {point.point_title || point.point_key || point.point_node_id}
                                        </Tag>
                                      ))}
                                    </Space>
                                    {errors.length ? <Alert type="warning" showIcon message={errors.join("；")} /> : null}
                                    <Flex justify="space-between" align="center" gap={8} wrap="wrap">
                                      <Button size="small" autoInsertSpace={false} disabled={!draftId} onClick={() => openDraftEditor(item)}>
                                        编辑
                                      </Button>
                                      <Space size={4}>
                                        <Popconfirm
                                          title={duplicateRisk ? "这道题可能重复，仍要发布吗？" : "发布这条待审题目？"}
                                          description={duplicateRisk ? duplicateRiskMessage(duplicateRisk) : undefined}
                                          onConfirm={() => (draftId ? publishDraft.mutate(draftId) : publishCandidate.mutate(candidateId))}
                                          disabled={Boolean(errors.length) || status !== "draft"}
                                        >
                                          <Button
                                            type="link"
                                            size="small"
                                            disabled={Boolean(errors.length) || status !== "draft"}
                                            loading={draftId ? publishDraft.isPending : publishCandidate.isPending}
                                          >
                                            发布
                                          </Button>
                                        </Popconfirm>
                                        <Button
                                          type="link"
                                        danger
                                        size="small"
                                        disabled={status !== "draft"}
                                        loading={draftId ? rejectDraft.isPending : rejectCandidate.isPending}
                                        onClick={() => (draftId ? rejectDraft.mutate(draftId) : rejectCandidate.mutate(candidateId))}
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
                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="设置题型和提示后生成待审题目" />
                          )}
                        </QueryState>
                      </div>
                    </div>

                    {workbenchTurns.length ? (
                      <details className="question-authoring-log">
                        <summary>生成记录（{workbenchTurns.length} 轮）</summary>
                        <div className="ai-workbench-chat-timeline">
                          {workbenchTurns.map((turn) => (
                            <div key={turn.id} className={`ai-chat-turn ai-chat-turn-${turn.role}`}>
                              <Text strong>{turn.role === "user" ? "老师" : "AI"}</Text>
                              <Text className="block-text">{turn.content}</Text>
                              {turn.error_state ? <Alert type="error" showIcon title="本轮生成失败" description={String(turn.error_state.message || "")} /> : null}
                            </div>
                          ))}
                        </div>
                      </details>
                    ) : null}
                  </Space>
                </Card>
              </div>

              <Card
                className="question-bank-question-panel"
                title="点位题目"
                extra={
                  <Space wrap>
                    <Select
                      allowClear
                      placeholder="题型"
                      value={questionType}
                      onChange={setQuestionType}
                      className="question-bank-compact-select"
                      options={[
                        { value: "single_choice", label: "选择" },
                        { value: "true_false", label: "判断" },
                        { value: "fill_blank", label: "填空" },
                      ]}
                    />
                    <Select
                      value={statusFilter}
                      onChange={setStatusFilter}
                      className="question-bank-compact-select"
                      options={[
                        { value: "all", label: "全部状态" },
                        { value: "published", label: "已发布" },
                        { value: "draft", label: "草稿" },
                        { value: "disabled", label: "已停用" },
                      ]}
                    />
                    <Input.Search
                      allowClear
                      placeholder="搜索题干或解析"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      onSearch={setSearch}
                      className="question-bank-catalog-search"
                    />
                  </Space>
                }
              >
                <QueryState loading={questions.isLoading} error={questions.error} empty={!visibleQuestions.length}>
                  <Table
                    rowKey="id"
                    size="middle"
                    dataSource={visibleQuestions}
                    pagination={{ pageSize: 8, showSizeChanger: false }}
                    onRow={(record) => ({ onClick: () => openQuestionDetail(record) })}
                    columns={[
                      { title: "题型", width: 76, dataIndex: "question_type", render: questionTypeLabel },
                      { title: "题干", dataIndex: "stem" },
                      {
                        title: "主点位",
                        width: 180,
                        render: (_: unknown, row: Question) => questionPointTitles(row)[0] || selectedPoint.title,
                      },
                      {
                        title: "证据",
                        width: 112,
                        render: (_: unknown, row: Question) => (
                          <Space orientation="vertical" size={2}>
                            {evidenceStatusTag(row)}
                            <Text type="secondary">{row.source_refs?.length || 0} 条</Text>
                          </Space>
                        ),
                      },
                      { title: "状态", width: 84, dataIndex: "status", render: questionBankStatusTag },
                    ]}
                  />
                </QueryState>
              </Card>

            </>
          ) : null}
        </div>
      </div>

      <Modal
        title="题目详情"
        open={detailOpen}
        width={920}
        onCancel={() => setDetailOpen(false)}
        footer={<Button onClick={() => setDetailOpen(false)}>关闭</Button>}
      >
        {selectedQuestion ? (
          <Space orientation="vertical" size={16} className="full question-detail-card">
            <Title level={4}>{selectedQuestion.stem}</Title>
            <Space wrap>
              <Tag color="blue">{questionTypeLabel(selectedQuestion.question_type)}</Tag>
              {questionBankStatusTag(selectedQuestion.status)}
              <Tag>{evidenceStatusText(selectedQuestion)}</Tag>
            </Space>
            {selectedQuestion.options?.length ? (
              <div className="question-options">
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
            <Descriptions size="small" column={1}>
              <Descriptions.Item label="答案">{answerText(selectedQuestion.answer)}</Descriptions.Item>
              <Descriptions.Item label="解析">{selectedQuestion.explanation || "暂无解析"}</Descriptions.Item>
              <Descriptions.Item label="主点位">{questionPointTitles(selectedQuestion)[0] || selectedPoint?.title || "-"}</Descriptions.Item>
            </Descriptions>
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
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择题目" />
        )}
      </Modal>

      <Modal
        title="编辑待审题目"
        open={Boolean(draftEditor)}
        width={760}
        onCancel={() => setDraftEditor(null)}
        footer={
          <Space>
            <Button onClick={() => setDraftEditor(null)}>取消</Button>
            <Button type="primary" loading={updateDraft.isPending} onClick={saveDraftEditor}>
              保存
            </Button>
          </Space>
        }
      >
        {draftEditor ? (
          <Space orientation="vertical" size={14} className="full question-draft-editor">
            <Alert type="info" showIcon message="保存后仍需点击发布，题目才会进入正式题库。" />
            <Space wrap>
              <Select
                value={draftEditor.questionType}
                onChange={(value) => setDraftEditor((current) => (current ? { ...current, questionType: value as Question["question_type"] } : current))}
                options={[
                  { value: "single_choice", label: "选择" },
                  { value: "true_false", label: "判断" },
                  { value: "fill_blank", label: "填空" },
                ]}
                className="question-bank-compact-select"
              />
            </Space>
            <label>
              <Text strong>题干</Text>
              <Input.TextArea
                rows={3}
                value={draftEditor.stem}
                onChange={(event) => setDraftEditor((current) => (current ? { ...current, stem: event.target.value } : current))}
              />
            </label>
            {draftEditor.questionType === "single_choice" ? (
              <label>
                <Text strong>选项</Text>
                <Input.TextArea
                  rows={5}
                  value={draftEditor.optionsText}
                  placeholder={"A. 选项内容\nB. 选项内容"}
                  onChange={(event) => setDraftEditor((current) => (current ? { ...current, optionsText: event.target.value } : current))}
                />
              </label>
            ) : null}
            <label>
              <Text strong>答案</Text>
              <Input.TextArea
                rows={draftEditor.questionType === "fill_blank" ? 3 : 2}
                value={draftEditor.answerText}
                placeholder={draftEditor.questionType === "fill_blank" ? "多个可接受答案用分号、逗号或换行分隔" : "选择题填写选项字母；判断题填写正确或错误"}
                onChange={(event) => setDraftEditor((current) => (current ? { ...current, answerText: event.target.value } : current))}
              />
            </label>
            <label>
              <Text strong>解析</Text>
              <Input.TextArea
                rows={4}
                value={draftEditor.explanation}
                onChange={(event) => setDraftEditor((current) => (current ? { ...current, explanation: event.target.value } : current))}
              />
            </label>
          </Space>
        ) : null}
      </Modal>

      <Drawer
        title="教材证据原文"
        open={Boolean(selectedEvidenceSource)}
        width={620}
        onClose={() => setSelectedEvidenceSource(null)}
        className="question-evidence-source-drawer"
      >
        {selectedEvidenceSource ? (
          <Space orientation="vertical" size={16} className="full">
            <div>
              <Text className="eyebrow">
                {textbookSectionLabels[String(selectedEvidenceSource.evidence_role || selectedEvidenceSource.section || "")] || "教材证据"}
              </Text>
              <Title level={4}>{sourceRefLabel(selectedEvidenceSource)}</Title>
            </div>
            <Descriptions size="small" column={1} bordered>
              <Descriptions.Item label="教材">
                {cleanSourceText(selectedEvidenceSource.source_file) || cleanSourceText(selectedEvidenceSource.source_title) || "-"}
              </Descriptions.Item>
              <Descriptions.Item label="页码">{sourcePageLabel(selectedEvidenceSource)}</Descriptions.Item>
              <Descriptions.Item label="章节路径">{sourceSectionPathLabel(selectedEvidenceSource)}</Descriptions.Item>
              <Descriptions.Item label="Chunk ID">{cleanSourceText(selectedEvidenceSource.chunk_id) || "-"}</Descriptions.Item>
              <Descriptions.Item label="Rerank 分数">{sourceScoreLabel(selectedEvidenceSource.rerank_score)}</Descriptions.Item>
            </Descriptions>
            <div className="question-evidence-source-text-card">
              <Text strong>原文</Text>
              {sourceEvidenceText(selectedEvidenceSource) ? (
                <div className="question-evidence-source-markdown">
                  <AssistantMarkdownContent text={sourceEvidenceMarkdown(selectedEvidenceSource)} />
                </div>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该证据没有可显示的原文" />
              )}
            </div>
          </Space>
        ) : null}
      </Drawer>
    </Space>
  );
}
