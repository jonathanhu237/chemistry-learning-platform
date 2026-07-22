import { isValidElement, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import katex from "katex";
import { AiMermaidBlock } from "../shared/markdown/AiMermaidBlock";
import {
  extractAiRichContentArtifacts,
  type AiRichContentArtifact,
  type AiRichContentOpenContext,
} from "../shared/markdown/aiRichContentArtifacts";
import { normalizeStudentMarkdown } from "../shared/markdown/markdownNormalize";
import "katex/dist/katex.min.css";
import "katex/contrib/mhchem";

function renderStudentKatex(latex: string, displayMode: boolean) {
  try {
    return katex.renderToString(latex, {
      displayMode,
      strict: "ignore",
      throwOnError: true,
      trust: false,
    });
  } catch {
    return "";
  }
}

function StudentKatex({ latex, displayMode }: { latex: string; displayMode: boolean }) {
  const html = useMemo(() => renderStudentKatex(latex, displayMode), [displayMode, latex]);
  if (!html) {
    return <code className="ai-md-inline-code">{latex}</code>;
  }
  return (
    <span
      className={displayMode ? "ai-md-katex ai-md-katex-display" : "ai-md-katex"}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

function ArtifactOpenButton({ artifact, context }: { artifact: AiRichContentArtifact; context: AiRichContentOpenContext }) {
  return (
    <button type="button" className="ai-md-artifact-open" onClick={() => context.onOpenArtifact(artifact)} aria-label={`查看${artifact.title}`}>
      <span>查看详情</span>
    </button>
  );
}

function markdownNodeStartLine(node: unknown): number | null {
  if (!node || typeof node !== "object") return null;
  const position = (node as { position?: { start?: { line?: unknown } } }).position;
  return typeof position?.start?.line === "number" ? position.start.line : null;
}

function createStudentMarkdownComponents(artifacts: AiRichContentArtifact[], artifactContext?: AiRichContentOpenContext): Components {
  const artifactFor = (kind: AiRichContentArtifact["kind"], node: unknown) => {
    const candidates = artifacts.filter((artifact) => artifact.kind === kind);
    const startLine = markdownNodeStartLine(node);
    return candidates.find((artifact) => artifact.startLine === startLine) || (candidates.length === 1 ? candidates[0] : undefined);
  };

  return {
    p({ children }) {
      return <p className="ai-md-paragraph">{children}</p>;
    },
    h1({ children }) {
      return <h4 className="ai-md-heading ai-md-heading-1">{children}</h4>;
    },
    h2({ children }) {
      return <h4 className="ai-md-heading ai-md-heading-2">{children}</h4>;
    },
    h3({ children }) {
      return <h4 className="ai-md-heading ai-md-heading-3">{children}</h4>;
    },
    h4({ children }) {
      return <h4 className="ai-md-heading">{children}</h4>;
    },
    hr() {
      return <hr className="ai-md-divider" />;
    },
    ul({ children }) {
      return <ul className="ai-md-list">{children}</ul>;
    },
    ol({ children }) {
      return <ol className="ai-md-list ai-md-ordered-list">{children}</ol>;
    },
    li({ children }) {
      return <li className="ai-md-list-item">{children}</li>;
    },
    table({ children, node }) {
      const artifact = artifactFor("table", node);
      return (
        <div className="ai-md-rich-block ai-md-table-block">
          <div className="ai-md-artifact-toolbar">
            <span>表格</span>
            {artifact && artifactContext ? <ArtifactOpenButton artifact={artifact} context={artifactContext} /> : null}
          </div>
          <div className="ai-md-table-wrap" role="region" aria-label="表格内容">
            <table className="ai-md-table">{children}</table>
          </div>
        </div>
      );
    },
    thead({ children }) {
      return <thead className="ai-md-table-head">{children}</thead>;
    },
    tbody({ children }) {
      return <tbody className="ai-md-table-body">{children}</tbody>;
    },
    th({ children }) {
      return <th className="ai-md-table-cell ai-md-table-header">{children}</th>;
    },
    td({ children }) {
      return <td className="ai-md-table-cell">{children}</td>;
    },
    input({ type, checked, disabled, ...props }) {
      if (type === "checkbox") {
        return <input {...props} type="checkbox" checked={checked} disabled className="ai-md-task-checkbox" aria-readonly="true" />;
      }
      return <input {...props} type={type} checked={checked} disabled={disabled} />;
    },
    strong({ children }) {
      return <strong className="ai-md-strong">{children}</strong>;
    },
    code({ className, children, node }) {
      const value = String(children).replace(/\n$/, "");
      const classValue = String(className || "");
      if (classValue.includes("language-mermaid")) {
        const artifact = artifactFor("mermaid", node);
        return <AiMermaidBlock chart={value} artifact={artifact} onOpenArtifact={artifactContext?.onOpenArtifact} />;
      }
      const isMath = classValue.includes("language-math") || classValue.includes("math-inline") || classValue.includes("math-display");
      if (isMath) {
        const displayMode = classValue.includes("math-display") || value.includes("\n");
        return <StudentKatex latex={value} displayMode={displayMode} />;
      }
      if (classValue || value.includes("\n")) {
        return <code className={className}>{children}</code>;
      }
      return <code className="ai-md-inline-code">{children}</code>;
    },
    pre({ children }) {
      if (isValidElement(children) && children.type === AiMermaidBlock) {
        return children;
      }
      return <pre className="ai-md-code-block">{children}</pre>;
    },
    a({ href, children }) {
      return (
        <a href={href} target="_blank" rel="noreferrer">
          {children}
        </a>
      );
    },
  };
}

export function AiStaticMarkdown({
  text,
  className = "",
  artifactContext,
}: {
  text: string | null | undefined;
  className?: string;
  artifactContext?: AiRichContentOpenContext;
}) {
  const value = normalizeStudentMarkdown(text);
  const artifacts = useMemo(
    () => (artifactContext ? extractAiRichContentArtifacts(value, artifactContext.messageId) : []),
    [artifactContext, value],
  );
  const components = createStudentMarkdownComponents(artifacts, artifactContext);
  if (!value.trim()) return null;
  return (
    <div className={["ai-markdown", className].filter(Boolean).join(" ")}>
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]} components={components}>
        {value}
      </ReactMarkdown>
    </div>
  );
}

export function AiMarkdown(props: { text: string | null | undefined; className?: string }) {
  return <AiStaticMarkdown {...props} />;
}
