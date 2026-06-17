import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import katex from "katex";
import "katex/dist/katex.min.css";
import "katex/contrib/mhchem";

function normalizeStudentMarkdown(text: string | null | undefined): string {
  return String(text || "")
    .replace(/\r\n/g, "\n")
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, content: string) => `$$${content}$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, content: string) => `$${content}$`);
}

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

const studentMarkdownComponents: Components = {
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
  strong({ children }) {
    return <strong className="ai-md-strong">{children}</strong>;
  },
  code({ className, children }) {
    const value = String(children).replace(/\n$/, "");
    const classValue = String(className || "");
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

export function AiMarkdown({ text, className = "" }: { text: string | null | undefined; className?: string }) {
  const value = normalizeStudentMarkdown(text);
  if (!value.trim()) return null;
  return (
    <div className={["ai-markdown", className].filter(Boolean).join(" ")}>
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} components={studentMarkdownComponents}>
        {value}
      </ReactMarkdown>
    </div>
  );
}
