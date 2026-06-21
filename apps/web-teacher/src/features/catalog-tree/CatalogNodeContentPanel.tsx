import { useEffect, useMemo, useRef, useState } from "react";
import { Button, Form, Input, Radio, Space, Tag, Typography, type FormInstance } from "antd";
import { RobotOutlined, SaveOutlined } from "@ant-design/icons";
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
  type CatalogNodeFormValues,
  type CatalogPointContentFormValues,
} from "./catalogTreeMappers";
import {
  buildEquationReviewModel,
  type CatalogEquationReviewCandidate,
} from "./catalogEquationReview";

const { Text } = Typography;

loader.config({ monaco });

const CHEM_REACTION_LANGUAGE = "chem-reaction";
const CHEM_REACTION_THEME = "chem-reaction-light";
let chemReactionEditorConfigured = false;

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

function CatalogEquationCodeEditor({
  value = "",
  onChange,
  placeholder,
}: {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
}) {
  const lineCount = value ? value.split(/\r?\n/).length : 1;
  const visibleLineCount = Math.max(4, lineCount);
  const editorHeight = Math.min(312, Math.max(124, visibleLineCount * 24 + 28));

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
        onChange={(nextValue) => onChange?.(nextValue ?? "")}
        options={chemReactionEditorOptions}
        loading={<div className="catalog-equation-monaco-loading">正在加载反应式编辑器...</div>}
        wrapperProps={{ "aria-label": "实验反应式输入" }}
      />
    </div>
  );
}

export function CatalogNodeContentPanel({
  detail,
  nodeForm,
  pointForm,
  principleMode,
  mutations,
  onSavePointContent,
  variant = "panel",
}: {
  detail: CatalogNodeDetail;
  nodeForm: FormInstance<CatalogNodeFormValues>;
  pointForm: FormInstance<CatalogPointContentFormValues>;
  principleMode?: string;
  mutations: CatalogMutations;
  onSavePointContent: (values: CatalogPointContentFormValues) => Promise<void>;
  variant?: "panel" | "task";
}) {
  const { node } = detail;
  const equationText = Form.useWatch("reaction_equations_text", pointForm) || "";
  const [equationPreview, setEquationPreview] = useState<CatalogEquationPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [assistLoading, setAssistLoading] = useState(false);
  const [assistMessage, setAssistMessage] = useState("");
  const [assistDrafts, setAssistDrafts] = useState<CatalogEquationAssistDraft[]>([]);
  const previewSeq = useRef(0);
  const reviewModel = useMemo(() => buildEquationReviewModel(equationPreview, assistDrafts), [equationPreview, assistDrafts]);
  const hasEquationInput = Boolean(equationText.trim());
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
    if (principleMode !== "equation") return;
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
  }, [equationText, principleMode]);

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
      return;
    }
    const current = equationText.trim();
    pointForm.setFieldValue("reaction_equations_text", [current, replacement].filter(Boolean).join("\n"));
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
        catalog_path_text: detail.breadcrumbs.map((item) => item.title).join(" / "),
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
      <section className="catalog-editor-section catalog-editor-panel-section">
        <div className="catalog-editor-section-intro">
          <Text strong>基础信息</Text>
          <Text type="secondary">目录负责学生端导航与分类，不承载点位知识或视频绑定。</Text>
        </div>
        <Form
          form={nodeForm}
          layout="vertical"
          onFinish={(values) => mutations.updateNode.mutate({ nodeId: node.node_id, payload: buildCatalogNodeUpdatePayload(values) })}
        >
          <Form.Item name="node_kind" hidden>
            <Input />
          </Form.Item>
          <Form.Item name="title" label="目录标题" rules={[{ required: true, message: "请输入目录标题" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="teacher_note" label="教学备注" extra="仅教师端可见，不进入学生端、学生搜索或题目证据链。">
            <Input.TextArea className="catalog-teacher-note" autoSize={{ minRows: 2, maxRows: 5 }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={mutations.updateNode.isPending}>
            保存目录内容
          </Button>
        </Form>
      </section>
    );
  }

  return (
    <section className={`catalog-editor-section catalog-editor-panel-section ${variant === "task" ? "is-task-window" : ""}`}>
      <div className="catalog-editor-section-heading">
        <div className="catalog-editor-section-intro">
          <Text strong>内容</Text>
          <Text type="secondary">维护教师备注、实验原理、现象解释和安全提示。</Text>
        </div>
      </div>
      <Form form={pointForm} layout="vertical" onFinish={onSavePointContent}>
        <Form.Item name="point_title" hidden>
          <Input type="hidden" />
        </Form.Item>
        <Form.Item name="teacher_note" label="教学备注" extra="仅教师端可见，不进入学生端、学生搜索或题目证据链。">
          <Input.TextArea className="catalog-teacher-note" autoSize={{ minRows: 2, maxRows: 5 }} />
        </Form.Item>
        <Form.Item name="principle_mode" label="实验原理形式" rules={[{ required: true }]}>
          <Radio.Group optionType="button" buttonStyle="solid">
            <Radio.Button value="equation">化学方程式</Radio.Button>
            <Radio.Button value="text">文字描述</Radio.Button>
          </Radio.Group>
        </Form.Item>
        {principleMode === "equation" ? (
          <div className="catalog-equation-natural-editor">
            <div className="catalog-equation-inline-help">
              <Text strong>实验反应式</Text>
              <span>
                直接输入或粘贴反应式，一行一个；条件、过量、酸碱环境或补充说明写在同一行的 <code>//</code> 后面。
              </span>
            </div>
            <div className="catalog-equation-workbench">
              <section className="catalog-equation-pane catalog-equation-preview-pane">
                <div className="catalog-equation-pane-heading">
                  <div>
                    <Text strong>反应式预览</Text>
                    <Text type="secondary">根据右侧输入实时渲染。</Text>
                  </div>
                </div>
                {previewError ? <div className="catalog-equation-natural-feedback is-error">{previewError}</div> : null}
                {previewLoading ? <div className="catalog-equation-natural-feedback">正在渲染预览...</div> : null}
                {reviewModel.rows.length || reviewModel.supplementalCandidates.length ? (
                  <div className="catalog-equation-natural-preview">
                    <div className="catalog-equation-natural-preview-title">
                      <Text strong>按输入渲染</Text>
                      <Space wrap>
                        <Text type="secondary">保存时以右侧输入为准，后端会生成 AI/检索可用的规范结构。</Text>
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
                ) : (
                  <div className="catalog-equation-natural-empty">
                    <Text strong>{hasEquationInput ? "等待预览" : "还没有预览"}</Text>
                    <Text type="secondary">
                      {hasEquationInput ? "输入稳定后会自动刷新左侧渲染。" : "右侧输入反应式后，这里会显示规范化渲染。"}
                    </Text>
                  </div>
                )}
                {assistMessage ? <div className="catalog-equation-natural-feedback">{assistMessage}</div> : null}
              </section>
              <section className="catalog-equation-pane catalog-equation-input-pane">
                <div className="catalog-equation-pane-heading">
                  <div>
                    <Text strong>输入反应式</Text>
                    <Text type="secondary">像代码编辑器一样按行维护；每一行对应左侧一个预览序号。</Text>
                  </div>
                </div>
                <Form.Item name="reaction_equations_text" rules={[{ required: true, message: "请输入实验反应式，或切换为文字描述" }]}>
                  <CatalogEquationCodeEditor placeholder={"例如：CL2+H2=HCL\nCl2 + 2KBr -> 2KCl + Br2\n氯气 + 氢气 = 氯化氢"} />
                </Form.Item>
                <div className="catalog-equation-natural-actions">
                  <div className="catalog-equation-natural-action-copy">
                    <Text type="secondary">默认采用右侧输入；需要进一步校对或补全时，再让 AI 基于当前内容给建议。</Text>
                  </div>
                  <Space wrap>
                    <Button type="primary" icon={<RobotOutlined />} loading={assistLoading} onClick={() => void runEquationAssist()}>
                      {hasEquationInput ? "AI 校对" : "AI 根据点位建议"}
                    </Button>
                  </Space>
                </div>
              </section>
            </div>
          </div>
        ) : (
          <Form.Item name="principle_text" label="文字原理" rules={[{ required: true, message: "请输入文字原理" }]}>
            <Input.TextArea autoSize={{ minRows: 3, maxRows: 7 }} />
          </Form.Item>
        )}
        <Form.Item name="phenomenon_explanation" label="现象解释" rules={[{ required: true, message: "请输入现象解释" }]}>
          <Input.TextArea autoSize={{ minRows: 3, maxRows: 7 }} />
        </Form.Item>
        <Form.Item name="safety_note" label="安全提示" rules={[{ required: true, message: "请输入安全提示" }]}>
          <Input.TextArea autoSize={{ minRows: 2, maxRows: 5 }} />
        </Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<SaveOutlined />}
          loading={mutations.savePointContent.isPending || mutations.updateNode.isPending}
        >
          保存点位内容
        </Button>
      </Form>
    </section>
  );
}
