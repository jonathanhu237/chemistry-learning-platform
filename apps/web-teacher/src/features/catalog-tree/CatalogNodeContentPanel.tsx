import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef, useState, type ReactNode } from "react";
import { Button, Form, Input, Modal, Radio, Space, Tag, Typography, type FormInstance } from "antd";
import { CheckCircleOutlined, ExclamationCircleOutlined, LoadingOutlined, RobotOutlined } from "@ant-design/icons";
import { Editor as MonacoEditor, loader, type BeforeMount } from "@monaco-editor/react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api.js";
import type { editor } from "monaco-editor/esm/vs/editor/editor.api.js";

import {
  assistCatalogReactionEquations,
  previewCatalogReactionEquations,
  type CatalogEquationAssistDraft,
  type CatalogEquationPreviewResponse,
  type CatalogNodeDetail,
} from "../../api/catalogTree";
import { AssistantMarkdownContent } from "../../lib/assistant-markdown";
import type { CatalogMutations } from "./catalogTreeHooks";
import {
  buildCatalogNodeUpdatePayload,
  catalogMissingLearningFieldLabels,
  type CatalogNodeFormValues,
  type CatalogPointContentFormValues,
} from "./catalogTreeMappers";
import {
  buildEquationReviewModel,
  type CatalogEquationReviewCandidate,
} from "./catalogEquationReview";
import { catalogPathLabel } from "./catalogPath";

const { Text, Title } = Typography;

loader.config({ monaco });

const CHEM_REACTION_LANGUAGE = "chem-reaction";
const CHEM_REACTION_THEME = "chem-reaction-light";
const CONTENT_AUTOSAVE_DELAY_MS = 900;
let chemReactionEditorConfigured = false;

type ContentAutoSaveStatus = "saved" | "dirty" | "saving" | "error";

function contentAutoSaveLabel(status: ContentAutoSaveStatus): string {
  if (status === "saving") return "正在保存";
  if (status === "dirty") return "有未保存更改";
  if (status === "error") return "保存失败";
  return "已保存";
}

function contentAutoSaveTitle(status: ContentAutoSaveStatus, error: string): string {
  if (status === "saving") return "正在自动保存当前内容";
  if (status === "dirty") return "停止输入后会自动保存";
  if (status === "error") return error || "保存失败，请继续编辑或稍后重试";
  return "所有更改已保存";
}

function contentAutoSaveIcon(status: ContentAutoSaveStatus) {
  if (status === "saving") return <LoadingOutlined />;
  if (status === "error") return <ExclamationCircleOutlined />;
  return <CheckCircleOutlined />;
}

function contentAutoSaveDisplayLabel(status: ContentAutoSaveStatus): string {
  if (status === "saving") return "正在保存";
  if (status === "dirty") return "有未保存更改";
  if (status === "error") return "保存失败";
  return "已保存";
}

function contentAutoSaveDisplayTitle(status: ContentAutoSaveStatus, error: string): string {
  if (status === "saving") return "正在自动保存当前内容";
  if (status === "dirty") return "停止输入后会自动保存";
  if (status === "error") return error || "保存失败，请继续编辑或稍后重试";
  return "所有更改已保存";
}

const chemReactionEditorOptions: editor.IStandaloneEditorConstructionOptions = {
  automaticLayout: true,
  minimap: { enabled: false },
  fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", monospace',
  fontSize: 14,
  fontWeight: "600",
  lineHeight: 24,
  lineNumbers: "on",
  lineNumbersMinChars: 2,
  lineDecorationsWidth: 10,
  glyphMargin: false,
  folding: false,
  overviewRulerLanes: 0,
  hideCursorInOverviewRuler: true,
  renderLineHighlight: "none",
  scrollBeyondLastLine: false,
  wordWrap: "off",
  tabSize: 2,
  insertSpaces: true,
  quickSuggestions: false,
  suggestOnTriggerCharacters: false,
  padding: { top: 12, bottom: 12 },
  scrollbar: {
    horizontalScrollbarSize: 10,
    verticalScrollbarSize: 10,
    alwaysConsumeMouseWheel: false,
  },
};

const configureChemReactionEditor: BeforeMount = (monaco) => {
  if (chemReactionEditorConfigured) return;
  chemReactionEditorConfigured = true;
  monaco.languages.register({ id: CHEM_REACTION_LANGUAGE });
  monaco.languages.setMonarchTokensProvider(CHEM_REACTION_LANGUAGE, {
    tokenizer: {
      root: [
        [/\/\/.*$/, "chem-comment"],
        [/(?:->|→|=>|=|⇌|↔)/, "chem-arrow"],
        [/[+]/, "chem-operator"],
        [/[()[\]{}]/, "chem-bracket"],
        [/\b(?:aq|s|l|g|Δ|hv|light|heat)\b/, "chem-condition"],
        [/\b\d+(?:\.\d+)?\b/, "chem-number"],
        [/\b(?:酸性|碱性|中性|过量|少量|浓|稀|加热|催化剂|水溶液|饱和)\b/, "chem-condition"],
        [/\b[A-Z][a-z]?(?:\d+)?(?:[A-Z][a-z]?(?:\d+)?)*(?:[+-])?\b/, "chem-species"],
        [/[\u4e00-\u9fa5]+/, "chem-text"],
      ],
    },
  });
  monaco.editor.defineTheme(CHEM_REACTION_THEME, {
    base: "vs",
    inherit: true,
    rules: [
      { token: "chem-species", foreground: "005826", fontStyle: "bold" },
      { token: "chem-arrow", foreground: "1f5f8f", fontStyle: "bold" },
      { token: "chem-operator", foreground: "7a4f00", fontStyle: "bold" },
      { token: "chem-number", foreground: "8a3ffc", fontStyle: "bold" },
      { token: "chem-bracket", foreground: "6b7280" },
      { token: "chem-condition", foreground: "b35c00", fontStyle: "bold" },
      { token: "chem-comment", foreground: "6a737d", fontStyle: "italic" },
      { token: "chem-text", foreground: "0f4c81" },
    ],
    colors: {
      "editor.background": "#fbfdfc",
      "editorLineNumber.foreground": "#8da39a",
      "editorLineNumber.activeForeground": "#005826",
      "editorCursor.foreground": "#005826",
      "editor.selectionBackground": "#cfe5d8",
      "editor.inactiveSelectionBackground": "#e9f2ed",
      "editor.lineHighlightBackground": "#00000000",
      "editorGutter.background": "#f3f7f5",
    },
  });
};

function splitEquationText(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function replaceEquationLine(value: string, rowOrder: number, replacement: string): string {
  const lines = value.split(/\r?\n/);
  const nonEmptyIndexes = lines
    .map((line, index) => ({ line, index }))
    .filter((item) => item.line.trim())
    .map((item) => item.index);
  const targetIndex = nonEmptyIndexes[rowOrder - 1] ?? lines.length;
  if (targetIndex >= lines.length) {
    return [...lines, replacement].join("\n").trim();
  }
  const next = [...lines];
  next[targetIndex] = replacement;
  return next.join("\n");
}

function inlineAnnotationSuffix(value: string): string {
  const delimiterIndex = value.indexOf("//");
  if (delimiterIndex < 0) return "";
  return value.slice(delimiterIndex).trim();
}

function currentEquationLine(value: string, rowOrder: number): string {
  const lines = value.split(/\r?\n/);
  const nonEmptyLines = lines.filter((line) => line.trim());
  return nonEmptyLines[rowOrder - 1] || "";
}

function preserveInlineAnnotationSuffix(currentLine: string, replacement: string): string {
  const currentSuffix = inlineAnnotationSuffix(currentLine);
  if (!currentSuffix || replacement.includes("//")) return replacement;
  return `${replacement.trim()} ${currentSuffix}`;
}

function principleModeLabel(mode: CatalogPointContentFormValues["principle_mode"]): string {
  return mode === "equation" ? "化学方程式" : "文字描述";
}

function RequiredFieldLabel({ children }: { children: string }) {
  return (
    <span className="catalog-required-field-label">
      <span aria-hidden="true">*</span>
      <strong>{children}</strong>
    </span>
  );
}

type CatalogEquationCodeEditorHandle = {
  focus: () => void;
};

const CatalogEquationCodeEditor = forwardRef<CatalogEquationCodeEditorHandle, {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: ReactNode;
}>(function CatalogEquationCodeEditor({
  value = "",
  onChange,
  placeholder,
}, ref) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const lineCount = value ? value.split(/\r?\n/).length : 1;
  const visibleLineCount = Math.max(4, lineCount);
  const editorHeight = Math.min(312, Math.max(124, visibleLineCount * 24 + 28));

  useImperativeHandle(ref, () => ({
    focus: () => editorRef.current?.focus(),
  }));

  return (
    <div className="catalog-equation-code-editor catalog-equation-monaco-editor">
      {!value ? <div className="catalog-equation-monaco-placeholder">{placeholder}</div> : null}
      <MonacoEditor
        className="catalog-equation-monaco"
        height={editorHeight}
        language={CHEM_REACTION_LANGUAGE}
        theme={CHEM_REACTION_THEME}
        value={value}
        beforeMount={configureChemReactionEditor}
        onMount={(editorInstance) => {
          editorRef.current = editorInstance;
        }}
        onChange={(nextValue) => onChange?.(nextValue ?? "")}
        options={chemReactionEditorOptions}
        loading={<div className="catalog-equation-monaco-loading">正在加载反应式编辑器...</div>}
        wrapperProps={{ "aria-label": "实验反应式输入" }}
      />
    </div>
  );
});

export function CatalogNodeContentPanel({
  detail,
  nodeForm,
  pointForm,
  principleMode,
  mutations,
  onSavePointContent,
  onLocalContentChange,
  variant = "panel",
}: {
  detail: CatalogNodeDetail;
  nodeForm: FormInstance<CatalogNodeFormValues>;
  pointForm: FormInstance<CatalogPointContentFormValues>;
  principleMode?: string;
  mutations: CatalogMutations;
  onSavePointContent: (values: CatalogPointContentFormValues, options?: { silent?: boolean }) => Promise<void>;
  onLocalContentChange?: () => void;
  variant?: "panel" | "task";
}) {
  const { node } = detail;
  const equationText = Form.useWatch("reaction_equations_text", pointForm) || "";
  const principleText = Form.useWatch("principle_text", pointForm) || "";
  const phenomenonExplanation = Form.useWatch("phenomenon_explanation", pointForm) || "";
  const safetyNote = Form.useWatch("safety_note", pointForm) || "";
  const watchedPrincipleMode = Form.useWatch("principle_mode", pointForm) || principleMode || "text";
  const activePrincipleMode = watchedPrincipleMode as CatalogPointContentFormValues["principle_mode"];
  const [equationPreview, setEquationPreview] = useState<CatalogEquationPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [assistLoading, setAssistLoading] = useState(false);
  const [assistMessage, setAssistMessage] = useState("");
  const [assistDrafts, setAssistDrafts] = useState<CatalogEquationAssistDraft[]>([]);
  const previewSeq = useRef(0);
  const autoSaveTimerRef = useRef<number | null>(null);
  const autoSaveVersionRef = useRef(0);
  const [autoSaveStatus, setAutoSaveStatus] = useState<ContentAutoSaveStatus>("saved");
  const [autoSaveError, setAutoSaveError] = useState("");
  const reviewModel = useMemo(() => buildEquationReviewModel(equationPreview, assistDrafts), [equationPreview, assistDrafts]);
  const hasEquationInput = Boolean(equationText.trim());
  const localMissingFieldKeys = useMemo(() => {
    const missing: Array<keyof typeof catalogMissingLearningFieldLabels> = [];
    const hasPrinciple = activePrincipleMode === "equation" ? Boolean(equationText.trim()) : Boolean(principleText.trim());
    if (!hasPrinciple) missing.push("principle");
    if (!phenomenonExplanation.trim()) missing.push("phenomenon");
    if (!safetyNote.trim()) missing.push("safety");
    return missing;
  }, [activePrincipleMode, equationText, phenomenonExplanation, principleText, safetyNote]);
  const missingFieldKeys = localMissingFieldKeys;
  const fieldTargetRefs = {
    principle: useRef<HTMLDivElement | null>(null),
    phenomenon: useRef<HTMLDivElement | null>(null),
    safety: useRef<HTMLDivElement | null>(null),
  };
  const equationEditorRef = useRef<CatalogEquationCodeEditorHandle | null>(null);
  const autoSavePill = (
    <span className={`catalog-autosave-status is-${autoSaveStatus}`} title={contentAutoSaveDisplayTitle(autoSaveStatus, autoSaveError)}>
      {contentAutoSaveIcon(autoSaveStatus)}
      {contentAutoSaveDisplayLabel(autoSaveStatus)}
    </span>
  );

  const clearAutoSaveTimer = () => {
    if (autoSaveTimerRef.current !== null) {
      window.clearTimeout(autoSaveTimerRef.current);
      autoSaveTimerRef.current = null;
    }
  };

  const focusMissingField = (fieldKey: keyof typeof catalogMissingLearningFieldLabels) => {
    const target = fieldTargetRefs[fieldKey].current;
    if (!target) return;
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => {
      if (fieldKey === "principle") {
        if (activePrincipleMode === "equation") {
          equationEditorRef.current?.focus();
          return;
        }
        target.querySelector<HTMLTextAreaElement>("textarea")?.focus();
        return;
      }
      const focusable = target.querySelector<HTMLElement>("textarea, input, button, [tabindex]:not([tabindex='-1'])");
      focusable?.focus();
    }, 160);
  };

  const runAutoSave = async (version: number) => {
    if (version !== autoSaveVersionRef.current) return;
    setAutoSaveStatus("saving");
    setAutoSaveError("");
    try {
      if (node.node_kind === "directory") {
        const values = {
          ...nodeForm.getFieldsValue(true),
          node_kind: node.node_kind,
        } as CatalogNodeFormValues;
        if (!values.title?.trim()) {
          if (version === autoSaveVersionRef.current) setAutoSaveStatus("dirty");
          return;
        }
        await mutations.updateNode.mutateAsync({ nodeId: node.node_id, payload: buildCatalogNodeUpdatePayload(values), silent: true });
      } else {
        const values = pointForm.getFieldsValue(true) as CatalogPointContentFormValues;
        const pointTitle = values.point_title || detail.point_content?.point_title || detail.node.title;
        await onSavePointContent({ ...values, point_title: pointTitle, principle_mode: values.principle_mode || "text" }, { silent: true });
      }
      if (version === autoSaveVersionRef.current) setAutoSaveStatus("saved");
    } catch (error) {
      if (version === autoSaveVersionRef.current) {
        setAutoSaveError(error instanceof Error ? error.message : "保存失败");
        setAutoSaveStatus("error");
      }
    }
  };

  const scheduleAutoSave = () => {
    onLocalContentChange?.();
    clearAutoSaveTimer();
    autoSaveVersionRef.current += 1;
    const version = autoSaveVersionRef.current;
    setAutoSaveStatus("dirty");
    setAutoSaveError("");
    autoSaveTimerRef.current = window.setTimeout(() => {
      autoSaveTimerRef.current = null;
      void runAutoSave(version);
    }, CONTENT_AUTOSAVE_DELAY_MS);
  };

  useEffect(() => {
    clearAutoSaveTimer();
    autoSaveVersionRef.current += 1;
    setAutoSaveStatus("saved");
    setAutoSaveError("");
    return clearAutoSaveTimer;
  }, [node.node_id, variant]);

  const requestPreview = async (textValue: string, seq: number) => {
    const rows = splitEquationText(textValue).map((rawText, index) => ({ raw_text: rawText, row_order: index + 1 }));
    if (!rows.length) {
      setEquationPreview(null);
      setPreviewLoading(false);
      setPreviewError("");
      return;
    }
    setPreviewLoading(true);
    setPreviewError("");
    try {
      const response = await previewCatalogReactionEquations(rows, textValue);
      if (seq === previewSeq.current) {
        setEquationPreview(response);
      }
    } catch (error) {
      if (seq === previewSeq.current) {
        setPreviewError(error instanceof Error ? error.message : "实时检查失败，请稍后重试。");
      }
    } finally {
      if (seq === previewSeq.current) {
        setPreviewLoading(false);
      }
    }
  };

  useEffect(() => {
    if (activePrincipleMode !== "equation") return;
    const seq = previewSeq.current + 1;
    previewSeq.current = seq;
    const textValue = equationText.trim();
    if (!textValue) {
      setEquationPreview(null);
      setPreviewLoading(false);
      setPreviewError("");
      return;
    }
    const timer = window.setTimeout(() => {
      void requestPreview(textValue, seq);
    }, 500);
    return () => window.clearTimeout(timer);
  }, [equationText, activePrincipleMode]);

  useEffect(() => {
    setAssistMessage("");
    setAssistDrafts([]);
  }, [equationText]);

  const applyCandidate = (candidate: CatalogEquationReviewCandidate) => {
    const replacement = candidate.replacement_text || candidate.draft_text || candidate.canonical_display;
    if (!replacement) return;
    if (candidate.row_order) {
      const currentLine = currentEquationLine(equationText, candidate.row_order);
      const replacementWithAnnotation = preserveInlineAnnotationSuffix(currentLine, replacement);
      pointForm.setFieldValue("reaction_equations_text", replaceEquationLine(equationText, candidate.row_order, replacementWithAnnotation));
      scheduleAutoSave();
      return;
    }
    const current = equationText.trim();
    pointForm.setFieldValue("reaction_equations_text", [current, replacement].filter(Boolean).join("\n"));
    scheduleAutoSave();
  };

  const clearEquationFeedback = () => {
    previewSeq.current += 1;
    setEquationPreview(null);
    setPreviewLoading(false);
    setPreviewError("");
    setAssistMessage("");
    setAssistDrafts([]);
  };

  const commitPrincipleModeSwitch = (nextMode: CatalogPointContentFormValues["principle_mode"]) => {
    const nextValues: Partial<CatalogPointContentFormValues> = { principle_mode: nextMode };
    if (activePrincipleMode === "equation") {
      nextValues.reaction_equations_text = "";
      nextValues.reaction_equations = [];
      nextValues.principle_equation = "";
      clearEquationFeedback();
    } else {
      nextValues.principle_text = "";
    }
    pointForm.setFieldsValue(nextValues);
    scheduleAutoSave();
  };

  const handlePrincipleModeChange = (event: { target: { value?: unknown } }) => {
    const nextMode = event.target.value as CatalogPointContentFormValues["principle_mode"];
    if (nextMode !== "equation" && nextMode !== "text") return;
    if (nextMode === activePrincipleMode) return;
    const currentContent = activePrincipleMode === "equation" ? equationText : principleText;
    if (!currentContent.trim()) {
      commitPrincipleModeSwitch(nextMode);
      return;
    }
    Modal.confirm({
      title: "切换实验原理形式？",
      content: `当前${principleModeLabel(activePrincipleMode)}内容不会继续保存。确认切换为${principleModeLabel(nextMode)}后，系统会清空当前${principleModeLabel(activePrincipleMode)}内容并自动保存。`,
      okText: "确认切换",
      cancelText: "放弃切换",
      okButtonProps: { danger: true },
      centered: true,
      onOk: () => commitPrincipleModeSwitch(nextMode),
    });
  };

  const runEquationAssist = async () => {
    setAssistLoading(true);
    setAssistMessage("");
    setAssistDrafts([]);
    try {
      const response = await assistCatalogReactionEquations({
        mode: "suggest",
        multiline_text: equationText,
        point_title: pointForm.getFieldValue("point_title") || detail.point_content?.point_title || detail.node.title,
        catalog_path_text: catalogPathLabel(detail.breadcrumbs, detail.node.chapter_id),
        phenomenon_explanation: pointForm.getFieldValue("phenomenon_explanation") || "",
        safety_note: pointForm.getFieldValue("safety_note") || "",
      });
      setAssistMessage(response.reason || "");
      setAssistDrafts(response.drafts || []);
    } catch (error) {
      setAssistMessage(error instanceof Error ? error.message : "助手暂时不可用。");
    } finally {
      setAssistLoading(false);
    }
  };

  if (node.node_kind === "directory") {
    return (
      <section className="catalog-editor-section catalog-editor-panel-section catalog-directory-panel-section">
        <div className="catalog-panel-title-row catalog-content-title-row">
          <div>
            <Title level={4}>目录信息</Title>
            <Text type="secondary">目录负责学生端导航与分类，不承载点位知识或视频绑定。编辑内容会自动保存；停止编辑 30 秒或连续编辑 3 分钟进行资源同步。</Text>
          </div>
          <div className="catalog-content-autosave-actions">{autoSavePill}</div>
        </div>
        <Form
          form={nodeForm}
          layout="vertical"
          onValuesChange={scheduleAutoSave}
        >
          <Form.Item name="node_kind" hidden>
            <Input />
          </Form.Item>
          <Form.Item name="title" hidden>
            <Input type="hidden" />
          </Form.Item>
          <section className="catalog-content-form-section catalog-content-note-section">
            <Form.Item name="teacher_note" label="教学备注" extra="仅教师端可见，不进入学生端、学生搜索或题目证据链。">
              <Input.TextArea className="catalog-teacher-note" autoSize={{ minRows: 2, maxRows: 5 }} />
            </Form.Item>
          </section>
        </Form>
      </section>
    );
  }

  return (
    <section className={`catalog-editor-section catalog-editor-panel-section ${variant === "task" ? "is-task-window" : ""}`}>
      <div className="catalog-panel-title-row catalog-content-title-row">
        <div>
          <Title level={4}>知识内容</Title>
          <Text type="secondary">维护教师备注、实验原理、现象解释和安全提示。 编辑内容会自动保存；停止编辑 30 秒或连续编辑 3 分钟进行资源同步。</Text>
        </div>
        <div className="catalog-content-autosave-actions">{autoSavePill}</div>
      </div>
      <Form form={pointForm} layout="vertical" onValuesChange={scheduleAutoSave}>
        <Form.Item name="point_title" hidden>
          <Input type="hidden" />
        </Form.Item>
        <Form.Item name="principle_mode" hidden>
          <Input type="hidden" />
        </Form.Item>
        <section className="catalog-content-form-section catalog-content-note-section">
          <Form.Item name="teacher_note" label="教学备注" extra="仅教师端可见，不进入学生端、学生搜索或题目证据链。">
            <Input.TextArea className="catalog-teacher-note" autoSize={{ minRows: 2, maxRows: 5 }} />
          </Form.Item>
        </section>
        <section className="catalog-content-form-section catalog-student-facing-section">
          <div className="catalog-content-section-heading">
            <div className="catalog-content-section-copy">
              <Text strong>学生可见内容</Text>
              <Text type="secondary">实验原理、现象解释和安全提示会进入学生端学习卡片、搜索和题目证据链。</Text>
            </div>
          </div>
          {missingFieldKeys.length ? (
            <div className="catalog-missing-fields-guide" role="note" aria-label="缺失学生可见内容">
              <ExclamationCircleOutlined />
              <span>还缺 {missingFieldKeys.length} 项：</span>
              {missingFieldKeys.map((fieldKey) => (
                <button key={fieldKey} type="button" onClick={() => focusMissingField(fieldKey)}>
                  {catalogMissingLearningFieldLabels[fieldKey]}
                </button>
              ))}
            </div>
          ) : null}
          <div ref={fieldTargetRefs.principle} className="catalog-content-principle-section" data-missing-field-target="principle">
          <div className="catalog-content-section-heading">
            <div className="catalog-content-section-copy">
              <RequiredFieldLabel>实验原理</RequiredFieldLabel>
              <Text type="secondary">
                {activePrincipleMode === "equation" ? (
                  <>
                    直接输入或粘贴反应式，一行一个；条件、过量、酸碱环境或补充说明写在同一行的 <code>//</code> 后面。
                  </>
                ) : (
                  "用文字说明实验原理。"
                )}
              </Text>
            </div>
            <div className="catalog-content-section-actions">
              {activePrincipleMode === "equation" ? (
                <Button type="primary" icon={<RobotOutlined />} loading={assistLoading} onClick={() => void runEquationAssist()}>
                  {hasEquationInput ? "AI 校对" : "AI 根据点位建议"}
                </Button>
              ) : null}
              <Radio.Group
                optionType="button"
                buttonStyle="solid"
                aria-label="实验原理形式"
                value={activePrincipleMode}
                onChange={handlePrincipleModeChange}
              >
                <Radio.Button value="equation">化学方程式</Radio.Button>
                <Radio.Button value="text">文字描述</Radio.Button>
              </Radio.Group>
            </div>
          </div>
          {activePrincipleMode === "equation" ? (
            <div className="catalog-equation-natural-editor">
              <div className="catalog-equation-workbench">
                <section className="catalog-equation-pane catalog-equation-input-pane">
                  <div className="catalog-equation-pane-heading">
                    <div>
                      <Text strong>输入反应式</Text>
                      <Text type="secondary">按行维护；每一行对应右侧一个预览序号。</Text>
                    </div>
                  </div>
                  <Form.Item name="reaction_equations_text" rules={[{ required: true, message: "请输入实验反应式，或切换为文字描述" }]}>
                    <CatalogEquationCodeEditor
                      ref={equationEditorRef}
                      placeholder={
                        [
                          <span className="catalog-equation-placeholder-label" key="label">例：</span>,
                          <span className="catalog-equation-placeholder-lines" key="lines">
                            {"Cl2 + 2KI -> 2KCl + I2 // 氯水氧化碘离子，溶液变棕黄\nBr2 + 2KI -> 2KBr + I2 // CCl4层呈紫红色，说明生成碘\nCl2 + 2NaOH -> NaCl + NaClO + H2O // 冷稀碱中歧化"}
                          </span>,
                        ]
                      }
                    />
                  </Form.Item>
                </section>
                <section className="catalog-equation-pane catalog-equation-preview-pane">
                  <div className="catalog-equation-pane-heading">
                    <div>
                      <Text strong>反应式预览</Text>
                      <Text type="secondary">保存时以输入为准，后端生成 AI/检索可用的规范结构。</Text>
                    </div>
                  </div>
                  {previewError ? <div className="catalog-equation-natural-feedback is-error">{previewError}</div> : null}
                  {previewLoading ? <div className="catalog-equation-natural-feedback">正在渲染预览...</div> : null}
                  {reviewModel.rows.length || reviewModel.supplementalCandidates.length ? (
                    <div className="catalog-equation-natural-preview">
                      <div className="catalog-equation-natural-preview-title">
                        <Text strong>按输入渲染</Text>
                        <Space wrap>
                          {reviewModel.rows.some((row) => row.candidates.length) ? (
                            <Button
                              className="catalog-equation-apply-button"
                              size="small"
                              onClick={() => reviewModel.rows.forEach((row) => row.candidates[0] && applyCandidate(row.candidates[0]))}
                            >
                              全部采用
                            </Button>
                          ) : null}
                        </Space>
                      </div>
                      <div className="catalog-equation-preview-scroll">
                        {reviewModel.rows.map(({ equation, candidates }) => {
                          return (
                            <div className="catalog-equation-natural-row" key={`${equation.row_order}-${equation.raw_text}`}>
                              <span className="catalog-equation-natural-index">{equation.row_order}</span>
                              <div className="catalog-equation-natural-result">
                                <div className="catalog-equation-natural-result-line">
                                  <div className="catalog-equation-natural-rendered">
                                    {equation.canonical_mhchem ? (
                                      <AssistantMarkdownContent text={`$${equation.canonical_mhchem}$`} inline />
                                    ) : (
                                      equation.canonical_display || equation.raw_text
                                    )}
                                    {equation.annotation_text ? (
                                      <div className="catalog-equation-inline-note">补充说明：{equation.annotation_text}</div>
                                    ) : null}
                                  </div>
                                </div>
                                {candidates.length ? (
                                  <div className="catalog-equation-natural-candidates">
                                    <Text className="catalog-equation-natural-candidates-title" type="secondary">AI 建议</Text>
                                    {candidates.map((candidate) => (
                                      <div className="catalog-equation-natural-candidate" key={candidate.key}>
                                        <div className="catalog-equation-natural-candidate-main">
                                          <Tag color={candidate.sources.includes("ai") ? "green" : "blue"}>{candidate.sourceLabel}</Tag>
                                          <div className="catalog-equation-natural-rendered">
                                            {candidate.canonical_mhchem ? (
                                              <AssistantMarkdownContent text={`$${candidate.canonical_mhchem}$`} inline />
                                            ) : (
                                              candidate.canonical_display
                                            )}
                                            {candidate.annotation_text ? (
                                              <div className="catalog-equation-inline-note">补充说明：{candidate.annotation_text}</div>
                                            ) : null}
                                          </div>
                                          <Button className="catalog-equation-apply-button" size="small" onClick={() => applyCandidate(candidate)}>
                                            采用
                                          </Button>
                                        </div>
                                        {candidate.rationale ? (
                                          <details className="catalog-equation-natural-details">
                                            <summary>查看 AI 分析</summary>
                                            <Text type="secondary">{candidate.rationale}</Text>
                                          </details>
                                        ) : null}
                                      </div>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                            </div>
                          );
                        })}
                        {reviewModel.supplementalCandidates.length ? (
                          <div className="catalog-equation-natural-supplemental">
                            <Text strong>AI 补充建议</Text>
                            {reviewModel.supplementalCandidates.map((candidate) => (
                              <div className="catalog-equation-natural-candidate" key={candidate.key}>
                                <div className="catalog-equation-natural-candidate-main">
                                  <Tag color="green">{candidate.sourceLabel}</Tag>
                                  <div className="catalog-equation-natural-rendered">
                                    {candidate.canonical_mhchem ? <AssistantMarkdownContent text={`$${candidate.canonical_mhchem}$`} inline /> : candidate.canonical_display}
                                    {candidate.annotation_text ? (
                                      <div className="catalog-equation-inline-note">补充说明：{candidate.annotation_text}</div>
                                    ) : null}
                                  </div>
                                  <Button className="catalog-equation-apply-button" size="small" onClick={() => applyCandidate(candidate)}>
                                    采用
                                  </Button>
                                </div>
                                {candidate.rationale ? (
                                  <details className="catalog-equation-natural-details">
                                    <summary>查看 AI 分析</summary>
                                    <Text type="secondary">{candidate.rationale}</Text>
                                  </details>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ) : (
                    <div className="catalog-equation-natural-empty">
                      <Text strong>{hasEquationInput ? "等待预览" : "还没有预览"}</Text>
                      <Text type="secondary">
                        {hasEquationInput ? "输入稳定后会自动刷新预览。" : "输入反应式后，这里会显示规范化渲染。"}
                      </Text>
                    </div>
                  )}
                  {assistMessage ? <div className="catalog-equation-natural-feedback">{assistMessage}</div> : null}
                </section>
              </div>
            </div>
          ) : (
            <Form.Item name="principle_text" rules={[{ required: true, message: "请输入文字原理" }]}>
              <Input.TextArea autoSize={{ minRows: 4, maxRows: 9 }} />
            </Form.Item>
          )}
          </div>
          <div className="catalog-student-facing-grid">
            <div ref={fieldTargetRefs.phenomenon} data-missing-field-target="phenomenon">
              <Form.Item
                name="phenomenon_explanation"
                label={<RequiredFieldLabel>现象解释</RequiredFieldLabel>}
                required={false}
                rules={[{ required: true, message: "请输入现象解释" }]}
              >
                <Input.TextArea autoSize={{ minRows: 4, maxRows: 9 }} />
              </Form.Item>
            </div>
            <div ref={fieldTargetRefs.safety} data-missing-field-target="safety">
              <Form.Item
                name="safety_note"
                label={<RequiredFieldLabel>安全提示</RequiredFieldLabel>}
                required={false}
                rules={[{ required: true, message: "请输入安全提示" }]}
              >
                <Input.TextArea autoSize={{ minRows: 4, maxRows: 9 }} />
              </Form.Item>
            </div>
          </div>
        </section>
      </Form>
    </section>
  );
}
