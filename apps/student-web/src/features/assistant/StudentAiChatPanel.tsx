import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import { Bot, LoaderCircle, Send, Sparkles } from "lucide-react";
import { AgentChatMessage, StudentAssistantFinalMetadata, errorMessage, streamStudentAssistantAsk } from "../../api";
import { MobileField } from "../../mobile/primitives";
import type { AssistantContext } from "./assistantContext";

type ChatMessage = AgentChatMessage & { metadata?: StudentAssistantFinalMetadata };

function assistantStatusLabel(status: string, loading: boolean): string {
  if (loading) return "正在生成";
  if (status === "ai") return "AI 已回答";
  if (status === "fallback") return "兜底回答";
  if (status === "error") return "请求失败";
  return "课程上下文已绑定";
}

function normalizeAssistantMetadata(value: unknown): StudentAssistantFinalMetadata | undefined {
  if (!value || typeof value !== "object") return undefined;
  return value as StudentAssistantFinalMetadata;
}

function renderInlineMarkdown(text: string): ReactNode[] {
  return text.split(/(`[^`]+`|\*\*[^*]+?\*\*)/g).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={`${part}-${index}`}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

function MarkdownLite({ content }: { content: string }) {
  const lines = content.split(/\r?\n/);
  return (
    <div className="ai-markdown">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (!trimmed) return <div className="ai-markdown-gap" key={`gap-${index}`} />;
        const bullet = trimmed.match(/^[-*]\s+(.+)$/);
        const ordered = trimmed.match(/^\d+[.)]\s+(.+)$/);
        if (bullet || ordered) {
          return (
            <p className="ai-markdown-bullet" key={`${trimmed}-${index}`}>
              <i>{ordered ? "•" : "•"}</i>
              <span>{renderInlineMarkdown((bullet || ordered)?.[1] || trimmed)}</span>
            </p>
          );
        }
        return <p key={`${trimmed}-${index}`}>{renderInlineMarkdown(trimmed)}</p>;
      })}
    </div>
  );
}

function AssistantSourceSummary({ metadata }: { metadata?: StudentAssistantFinalMetadata }) {
  const sources = Array.isArray(metadata?.sources) ? metadata.sources.slice(0, 3) : [];
  const sourceCount = typeof metadata?.source_count === "number" ? metadata.source_count : sources.length;
  if (!sourceCount && !sources.length) return null;
  return (
    <div className="ai-source-summary">
      <span>引用来源 {sourceCount || sources.length}</span>
      {sources.length ? (
        <div>
          {sources.map((source, index) => (
            <small key={`${source.chunk_id || source.title || "source"}-${index}`}>
              {source.title || source.section || source.chunk_id || "课程资料"}
            </small>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function StudentAiChatPanel({
  context,
}: {
  context: AssistantContext;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("idle");
  const streamRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
    setInput("");
    setStatus("idle");
    setLoading(false);
  }, [context.context_type, context.context_title, context.experiment_id, context.chapter_id]);

  useEffect(() => {
    if (!streamRef.current) return;
    if (typeof streamRef.current.scrollTo === "function") {
      streamRef.current.scrollTo({ top: streamRef.current.scrollHeight });
      return;
    }
    streamRef.current.scrollTop = streamRef.current.scrollHeight;
  }, [messages, loading]);

  const submitQuestion = async (questionText?: string) => {
    const question = (questionText || input).trim();
    if (!question || loading) return;
    const history = messages.slice(-10).map(({ role, content }) => ({ role, content }));
    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: question }, { role: "assistant", content: "" }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setStatus("streaming");
    let answer = "";
    try {
      await streamStudentAssistantAsk(
        {
          ...context,
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

  return (
    <section className="ai-chat-panel" role="region" aria-label="AI 学习助手对话">
      <header className="ai-chat-head">
        <div>
          <span>
            <Sparkles size={14} />
            当前内容
          </span>
          <h2>{context.context_title}</h2>
        </div>
      </header>

      <div className="ai-chat-stream" aria-live="polite" ref={streamRef}>
        {!messages.length ? (
          <div className="ai-empty-bubble">
            <Bot size={18} />
            <p>可以问我实验现象、原理、复习顺序和知识点。</p>
          </div>
        ) : null}
        {messages.map((message, index) => (
          <div className={`ai-message ${message.role}`} key={`${message.role}-${index}`}>
            {message.role === "assistant" ? (
              <>
                <MarkdownLite content={message.content || (loading ? "正在生成..." : "")} />
                <AssistantSourceSummary metadata={message.metadata} />
              </>
            ) : (
              message.content
            )}
          </div>
        ))}
      </div>

      <div className="ai-quick-prompts" aria-label="快捷问题">
        {context.prompts.map((prompt) => (
          <button type="button" key={prompt} disabled={loading} onClick={() => void submitQuestion(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <form className="ai-chat-compose" onSubmit={handleSubmit}>
        <MobileField
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="问当前学习内容"
          aria-label="输入给 AI 的问题"
        />
        <button type="submit" disabled={!input.trim() || loading} aria-label="发送问题">
          {loading ? <LoaderCircle className="spin" size={17} /> : <Send size={17} />}
        </button>
      </form>
      <div className="ai-chat-status">{assistantStatusLabel(status, loading)}</div>
    </section>
  );
}
