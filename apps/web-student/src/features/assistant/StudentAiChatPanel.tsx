import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, Bot, CheckCircle2, LoaderCircle, RotateCcw, Send, Sparkles, XCircle } from "lucide-react";
import { AgentChatMessage, StudentAssistantFinalMetadata, errorMessage, streamStudentAssistantAsk } from "../../api";
import { MobileTextArea } from "../../mobile/primitives";
import { AiMarkdownBlock } from "../../shared/markdown/AiMarkdownBlock";
import { defaultAssistantContext, type AssistantContext } from "./assistantContext";
import {
  assistantContextHint,
  assistantContextTypeLabel,
  assistantStarterIntents,
  buildStarterQuestion,
  isGlobalAssistantContext,
  type AssistantStarterIntent,
} from "./assistantStarter";

type ChatMessage = AgentChatMessage & { metadata?: StudentAssistantFinalMetadata };

function assistantStreamPhaseLabel(status: string, hasAnswer: boolean): string {
  if (hasAnswer) return "正在生成回答";
  const text = String(status || "");
  if (text.includes("搜索") || text.includes("证据") || text.includes("RAG") || text.includes("资料")) return "正在检索课程资料";
  if (text.includes("判断") || text.includes("安全") || text.includes("问题")) return "正在判断问题范围";
  if (text.includes("返回")) return "正在返回学习助手";
  return "正在生成回答";
}

function normalizeAssistantMetadata(value: unknown): StudentAssistantFinalMetadata | undefined {
  if (!value || typeof value !== "object") return undefined;
  return value as StudentAssistantFinalMetadata;
}

function AssistantSourceSummary({ metadata }: { metadata?: StudentAssistantFinalMetadata }) {
  const sources = Array.isArray(metadata?.sources) ? metadata.sources.slice(0, 3) : [];
  const sourceCount = typeof metadata?.source_count === "number" ? metadata.source_count : sources.length;
  if (!sourceCount && !sources.length) return null;
  return (
    <div className="ai-source-summary">
      <span>引用资料 {sourceCount || sources.length}</span>
    </div>
  );
}

function AssistantSkeleton() {
  return (
    <div className="ai-message-skeleton" aria-hidden="true">
      <span />
      <span />
      <span />
    </div>
  );
}

function AssistantStarterSurface({
  selectedIntent,
  intents,
  previewQuestion,
  loading,
  onSelectIntent,
  onLaunchPreview,
}: {
  selectedIntent: AssistantStarterIntent;
  intents: AssistantStarterIntent[];
  previewQuestion: string;
  loading: boolean;
  onSelectIntent: (intent: AssistantStarterIntent) => void;
  onLaunchPreview: () => void;
}) {
  const isCustom = selectedIntent.id === "custom";
  return (
    <div className="ai-starter-surface">
      <section className="ai-starter-card" aria-label="选择提问方向">
        <div className="ai-starter-heading">
          <p>你想先问哪一类？</p>
          <span>选择一个方向，AI 会按当前课程或点位上下文整理问题。</span>
        </div>
        <div className="ai-starter-intents">
          {intents.map((intent) => (
            <button
              type="button"
              key={intent.id}
              className={selectedIntent.id === intent.id ? "selected" : ""}
              onClick={() => onSelectIntent(intent)}
              disabled={loading}
            >
              <strong>{intent.label}</strong>
              <small>{intent.description}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="ai-starter-preview" aria-label="准备提问">
        <p>准备提问</p>
        {previewQuestion ? (
          <blockquote>{previewQuestion}</blockquote>
        ) : (
          <blockquote>可以直接在下方输入自己的问题。</blockquote>
        )}
        <button type="button" onClick={onLaunchPreview} disabled={loading || isCustom || !previewQuestion.trim()}>
          <span>{isCustom ? "请在下方输入" : "发送这个问题"}</span>
          <ArrowRight size={16} />
        </button>
      </section>
    </div>
  );
}

export function StudentAiChatPanel({
  context,
  onResetContext,
}: {
  context: AssistantContext;
  onResetContext: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("idle");
  const [selectedIntentId, setSelectedIntentId] = useState<string>("");
  const [activeContext, setActiveContext] = useState<AssistantContext>(context);
  const streamRef = useRef<HTMLDivElement>(null);

  const starterIntents = useMemo(() => assistantStarterIntents(activeContext), [activeContext]);
  const selectedIntent = starterIntents.find((intent) => intent.id === selectedIntentId) || starterIntents[0];
  const previewQuestion = selectedIntent ? buildStarterQuestion(selectedIntent, activeContext) : "";
  const contextMeta = [
    activeContext.chapter_id,
    activeContext.point_node_id ? "已绑定点位" : "",
    activeContext.catalog_path?.length ? activeContext.catalog_path.join(" / ") : "",
  ]
    .filter(Boolean)
    .join(" · ");

  useEffect(() => {
    setActiveContext(context);
    setMessages([]);
    setInput("");
    setStatus("idle");
    setLoading(false);
    setSelectedIntentId("");
  }, [
    context.context_type,
    context.context_title,
    context.experiment_id,
    context.chapter_id,
    context.point_node_id,
    context.source_node_id,
    JSON.stringify(context.catalog_path || []),
  ]);

  useEffect(() => {
    if (!selectedIntent || starterIntents.some((intent) => intent.id === selectedIntentId)) return;
    setSelectedIntentId(starterIntents[0]?.id || "");
  }, [selectedIntent, selectedIntentId, starterIntents]);

  useEffect(() => {
    if (!streamRef.current) return;
    if (typeof streamRef.current.scrollTo === "function") {
      streamRef.current.scrollTo({ top: streamRef.current.scrollHeight });
      return;
    }
    streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages, loading]);

  const handleResetContext = () => {
    setActiveContext(defaultAssistantContext());
    setMessages([]);
    setInput("");
    setLoading(false);
    setStatus("idle");
    setSelectedIntentId("");
    onResetContext();
  };

  const submitQuestion = async (questionText?: string, overrideContext?: AssistantContext) => {
    const question = (questionText || input).trim();
    if (!question || loading) return;
    const requestContext = overrideContext || activeContext;
    const history = messages.slice(-10).map(({ role, content }) => ({ role, content }));
    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: question }, { role: "assistant", content: "" }];
    setActiveContext(requestContext);
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setStatus("streaming");
    let answer = "";
    try {
      await streamStudentAssistantAsk(
        {
          ...requestContext,
          question,
          conversation_history: history,
        },
        (event) => {
          if (event.event === "status" && typeof event.message === "string") {
            setStatus(event.message);
            return;
          }
          if (event.event === "delta" && typeof event.delta === "string") {
            answer += event.delta;
            setMessages((current) => {
              const updated = [...current];
              const last = updated[updated.length - 1];
              if (last?.role === "assistant") updated[updated.length - 1] = { ...last, content: answer };
              return updated;
            });
            return;
          }
          if (event.event === "replace" && typeof event.answer === "string") {
            answer = event.answer;
            setMessages((current) => {
              const updated = [...current];
              const last = updated[updated.length - 1];
              if (last?.role === "assistant") updated[updated.length - 1] = { ...last, content: answer };
              return updated;
            });
            return;
          }
          if (event.event === "error") {
            throw new Error(typeof event.message === "string" ? event.message : "AI 请求失败");
          }
          if (event.event === "final") {
            const metadata = normalizeAssistantMetadata(event.response);
            if (metadata && typeof metadata.text === "string" && !answer.trim()) {
              answer = metadata.text;
            }
            setMessages((current) => {
              const updated = [...current];
              const last = updated[updated.length - 1];
              if (last?.role === "assistant") updated[updated.length - 1] = { ...last, content: answer || last.content, metadata };
              return updated;
            });
            setStatus("ai");
          }
        },
      );
      if (!answer.trim()) {
        setMessages((current) => {
          const updated = [...current];
          const last = updated[updated.length - 1];
          if (last?.role === "assistant") updated[updated.length - 1] = { ...last, content: "AI 暂时没有生成有效回答。" };
          return updated;
        });
      }
      setStatus("ai");
    } catch (requestError) {
      const message = errorMessage(requestError);
      setStatus("error");
      setMessages((current) => {
        const updated = [...current];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant") updated[updated.length - 1] = { ...last, content: message };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submitQuestion();
  };

  const handleLaunchPreview = () => {
    void submitQuestion(previewQuestion, activeContext);
  };

  return (
    <section className="ai-chat-panel" role="region" aria-label="AI 学习助手对话">
      <header className="ai-chat-head">
        <div>
          <span>
            <Sparkles size={14} />
            当前内容
          </span>
          <h2>{activeContext.context_title}</h2>
          <small>
            <b>{assistantContextTypeLabel(activeContext)}</b>
            {contextMeta ? <span>{contextMeta}</span> : null}
            <span>{assistantContextHint(activeContext)}</span>
          </small>
        </div>
        {!isGlobalAssistantContext(activeContext) ? (
          <button type="button" onClick={handleResetContext} aria-label="切回全局课程问答并开始新对话">
            <RotateCcw size={16} />
          </button>
        ) : null}
      </header>

      <div className="ai-chat-stream" aria-live="polite" ref={streamRef}>
        {!messages.length ? (
          <div className="ai-starter-shell">
            <AssistantStarterSurface
              selectedIntent={selectedIntent}
              intents={starterIntents}
              previewQuestion={previewQuestion}
              loading={loading}
              onSelectIntent={(intent) => setSelectedIntentId(intent.id)}
              onLaunchPreview={handleLaunchPreview}
            />
          </div>
        ) : null}
        {messages.map((message, index) => {
          const isActiveAssistant = message.role === "assistant" && loading && index === messages.length - 1;
          const isLastError = message.role === "assistant" && status === "error" && index === messages.length - 1;
          const assistantState = isLastError ? "error" : isActiveAssistant ? "running" : "done";
          return (
            <div className={`ai-message ${message.role} ${message.role === "assistant" ? assistantState : ""}`} key={`${message.role}-${index}`}>
              {message.role === "assistant" ? (
                <>
                  <div className="ai-message-meta">
                    <span>
                      <Bot size={14} />
                      学习助手
                    </span>
                    <em>
                      {isLastError ? <XCircle size={13} /> : isActiveAssistant ? <LoaderCircle className="spin" size={13} /> : <CheckCircle2 size={13} />}
                      {isLastError ? "失败" : isActiveAssistant ? "生成中" : "完成"}
                    </em>
                  </div>
                  {isActiveAssistant ? (
                    <div className="ai-stream-progress">
                      <span aria-hidden="true">
                        <i />
                        <i />
                        <i />
                      </span>
                      <strong>{assistantStreamPhaseLabel(status, Boolean(message.content.trim()))}</strong>
                    </div>
                  ) : null}
                  {message.content.trim() ? <AiMarkdownBlock text={message.content} /> : isActiveAssistant ? <AssistantSkeleton /> : null}
                  <AssistantSourceSummary metadata={message.metadata} />
                </>
              ) : (
                message.content
              )}
            </div>
          );
        })}
      </div>

      {messages.length ? (
        <div className="ai-quick-prompts" aria-label="快捷问题">
          {activeContext.prompts.map((prompt) => (
            <button type="button" key={prompt} disabled={loading} onClick={() => void submitQuestion(prompt)}>
              {prompt}
            </button>
          ))}
        </div>
      ) : null}

      <form className="ai-chat-compose" onSubmit={handleSubmit}>
        <MobileTextArea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="输入自己的问题"
          aria-label="输入给 AI 的问题"
          rows={1}
          maxLength={1600}
          disabled={loading}
        />
        <button type="submit" disabled={!input.trim() || loading} aria-label="发送问题">
          {loading ? <LoaderCircle className="spin" size={17} /> : <Send size={17} />}
        </button>
      </form>
    </section>
  );
}
