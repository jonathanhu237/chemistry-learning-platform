import { isValidElement, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import katex from "katex";
import "katex/dist/katex.min.css";
import "katex/contrib/mhchem";
import { Typography } from "antd";

import { getAuthToken } from "../../api/auth";
import { apiBase } from "../../api/http";

const assistantFencedBlockPattern = /(```[\s\S]*?```)/;
const assistantMathSpanPattern = /(\$\$[\s\S]*?\$\$|\$(?:\\.|[^$])+\$)/;
const assistantLooseChemReactionPattern =
  /\\(ce|ch)\s*(?!\{)([-+A-Za-z0-9\s\\_^{}().·]*?(?:-{1,3}\s*>|=>|<=>|→|⇌)[-+A-Za-z0-9\s\\_^{}().·]*)/g;
const assistantLooseChemCommandPattern =
  /\\(ce|ch)\s*(?!\{)((?:[A-Z0-9][A-Za-z0-9+\-().=<>·]*|[_^]\{[^{}]*\}|[_^](?:[+\-]?\d+[+\-]?|[+\-]))+)/g;
const assistantBrokenUnitDollarPattern =
  /\b(mol|mmol)\s*\\cdot\s*\$+\s*L\s*\^\s*\{?\s*(-?\d+)\s*\}?/gi;
const assistantUnitExpressionPattern =
  /((?:\d+(?:\.\d+)?\s*)?)(\b(?:mol|mmol))\s*\\cdot\s*L\s*\^\s*\{?\s*(-?\d+)\s*\}?/gi;
const assistantBareFormulaPattern =
  /(?:\d+(?:\.\d+)?\s*(?:\\,)?\s*\\mathrm\s*\{(?:[^{}]|\{[^{}]*\})*\}|\\(?:ce|ch|mathrm|text)\s*\{(?:[^{}]|\{[^{}]*\})*\}|\\(?:rightarrow|to|leftarrow|rightleftharpoons|Delta|delta|ominus|cdot|times|pm|circ|alpha|beta|gamma)\b)/g;

function normalizeAssistantMathDelimiters(text: string) {
  return text
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, content: string) => `$$${content}$$`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, content: string) => `$${content}$`);
}

function normalizeAssistantBrokenUnitText(text: string) {
  return text.replace(
    assistantBrokenUnitDollarPattern,
    (_match: string, unit: string, power: string) => `${unit}\\cdot L^{${power.replace(/\s+/g, "")}}`,
  );
}

function normalizeAssistantChemCommandAliases(text: string) {
  return text.replace(/\\ch\b/g, "\\ce");
}

function wrapBareAssistantFormulaCommands(text: string) {
  return text
    .split(assistantMathSpanPattern)
    .map((part, index) => {
      if (!part || index % 2 === 1) return part;
      const withUnits = part.includes("\\mathrm")
        ? part
        : part.replace(assistantUnitExpressionPattern, (_match: string, amount: string, unit: string, power: string) => {
            const prefix = amount.trim() ? `${amount.trim()}\\,` : "";
            return `$${prefix}\\mathrm{${unit}\\cdot L^{${power.replace(/\s+/g, "")}}}$`;
          });
      return withUnits
        .split(assistantMathSpanPattern)
        .map((nestedPart, nestedIndex) => {
          if (!nestedPart || nestedIndex % 2 === 1) return nestedPart;
          return nestedPart.replace(assistantBareFormulaPattern, (match) => `$${match}$`);
        })
        .join("");
    })
    .join("");
}

function normalizeAssistantChemReactionBody(body: string) {
  return body
    .replace(/\\(?:ce|ch)\s*\{([^{}]*)\}/g, "$1")
    .replace(assistantLooseChemCommandPattern, (_, _command: string, formula: string) => formula)
    .replace(/-{1,3}\s*>|=>|→/g, "->")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeLooseAssistantChemCommands(text: string) {
  const normalizedReactions = text.replace(
    assistantLooseChemReactionPattern,
    (_, command: string, formula: string) => `\\${command}{${normalizeAssistantChemReactionBody(formula)}}`,
  );
  return normalizedReactions.replace(
    assistantLooseChemCommandPattern,
    (_, command: string, formula: string) => `\\${command}{${formula}}`,
  );
}

function sanitizeLatexCommandsForText(value: string) {
  return value
    .replace(/\\(?:ce|ch|mathrm|text)\s*\{((?:[^{}]|\{[^{}]*\})*)\}/g, "$1")
    .replace(/\\left|\\right/g, "")
    .replace(/\\Delta/g, "Δ")
    .replace(/\\delta/g, "δ")
    .replace(/\\ominus/g, "⊖")
    .replace(/\\rightleftharpoons/g, "⇌")
    .replace(/\\rightarrow|\\to/g, "→")
    .replace(/\\leftarrow/g, "←")
    .replace(/\\cdot/g, "·")
    .replace(/\\times/g, "×")
    .replace(/\\pm/g, "±")
    .replace(/\\circ/g, "°")
    .replace(/\\,/g, " ")
    .replace(/\\[a-zA-Z]+/g, "")
    .replace(/[{}]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function mathSegmentIsRenderable(latex: string, displayMode: boolean) {
  try {
    katex.renderToString(latex, {
      displayMode,
      strict: "ignore",
      throwOnError: true,
      trust: false,
    });
    return true;
  } catch {
    return false;
  }
}

function renderAssistantKatexHtml(latex: string, displayMode: boolean) {
  return katex.renderToString(latex, {
    displayMode,
    strict: "ignore",
    throwOnError: true,
    trust: false,
  });
}

function AssistantKatex({
  latex,
  displayMode,
}: {
  latex: string;
  displayMode: boolean;
}) {
  const html = useMemo(() => {
    try {
      return renderAssistantKatexHtml(latex, displayMode);
    } catch {
      return "";
    }
  }, [displayMode, latex]);

  if (!html) {
    const fallback = sanitizeLatexCommandsForText(latex);
    return <span className="assistant-math-fallback">{fallback || latex}</span>;
  }

  const className = displayMode ? "assistant-katex assistant-katex-display" : "assistant-katex";
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}

function sanitizeInvalidAssistantMathSegments(text: string) {
  return text
    .split(assistantMathSpanPattern)
    .map((part, index) => {
      if (!part || index % 2 === 0) return part;
      const displayMode = part.startsWith("$$");
      const body = displayMode ? part.slice(2, -2) : part.slice(1, -1);
      if (mathSegmentIsRenderable(body, displayMode)) return part;
      return sanitizeLatexCommandsForText(body);
    })
    .join("");
}

export function normalizeAssistantMarkdownMath(text: string | null | undefined) {
  const value = String(text || "");
  if (!value) return "";
  return value
    .split(assistantFencedBlockPattern)
    .map((block, index) => {
      if (!block || index % 2 === 1) return block;
      const normalized = wrapBareAssistantFormulaCommands(
        normalizeLooseAssistantChemCommands(
          normalizeAssistantChemCommandAliases(normalizeAssistantMathDelimiters(normalizeAssistantBrokenUnitText(block))),
        ),
      );
      return sanitizeInvalidAssistantMathSegments(normalized);
    })
    .join("");
}

function createAssistantMarkdownComponents(inline: boolean): Components {
  return {
    p({ children }) {
      if (inline) return <>{children}</>;
      return <Typography.Paragraph className="assistant-md-paragraph">{children}</Typography.Paragraph>;
    },
    h1({ children }) {
      return <div className="assistant-md-heading level-1">{children}</div>;
    },
    h2({ children }) {
      return <div className="assistant-md-heading level-2">{children}</div>;
    },
    h3({ children }) {
      return <div className="assistant-md-heading level-3">{children}</div>;
    },
    h4({ children }) {
      return <div className="assistant-md-heading level-4">{children}</div>;
    },
    ul({ children }) {
      if (inline) return <>{children}</>;
      return <ul className="assistant-md-list">{children}</ul>;
    },
    ol({ children }) {
      if (inline) return <>{children}</>;
      return <ol className="assistant-md-list assistant-md-ordered-list">{children}</ol>;
    },
    li({ children }) {
      if (inline) return <span>{children}</span>;
      return <li className="assistant-md-list-item">{children}</li>;
    },
    code({ className, children }) {
      const value = String(children).replace(/\n$/, "");
      const classValue = String(className || "");
      const isMath = classValue.includes("language-math") || classValue.includes("math-inline") || classValue.includes("math-display");
      if (isMath) {
        const displayMode = classValue.includes("math-display") || value.includes("\n");
        return <AssistantKatex latex={value} displayMode={displayMode} />;
      }
      if (classValue || value.includes("\n")) {
        return <code className={className}>{value}</code>;
      }
      return <code className="assistant-md-inline-code">{value}</code>;
    },
    pre({ children }) {
      const child = Array.isArray(children) ? children[0] : children;
      if (isValidElement<{ className?: string }>(child)) {
        const classValue = String(child.props.className || "");
        if (classValue.includes("language-math") || classValue.includes("math-display")) {
          return <div className="assistant-md-math-block">{children}</div>;
        }
      }
      return <pre className="assistant-md-code">{children}</pre>;
    },
    img({ alt, src }) {
      return <AssistantMarkdownImage alt={String(alt || "")} src={String(src || "")} />;
    },
    a({ children, href }) {
      return (
        <a href={href} target="_blank" rel="noreferrer">
          {children}
        </a>
      );
    },
  };
}

export function AssistantMarkdownContent({
  text,
  inline = false,
}: {
  text: string | null | undefined;
  inline?: boolean;
}) {
  const value = normalizeAssistantMarkdownMath(text);
  if (!value.trim()) return null;
  const Wrapper = inline ? "span" : "div";
  return (
    <Wrapper className={inline ? "assistant-markdown assistant-markdown-inline" : "assistant-markdown"}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        components={createAssistantMarkdownComponents(inline)}
      >
        {value}
      </ReactMarkdown>
    </Wrapper>
  );
}

export function renderAssistantInlineMarkdown(text: string | null | undefined): ReactNode {
  return <AssistantMarkdownContent text={text} inline />;
}

function resolveMarkdownImageUrl(src: string) {
  const value = src.trim();
  if (value.startsWith("/")) return `${apiBase}${value}`;
  return value;
}

function cleanAssistantImageCaption(value: string) {
  let text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) return "";
  const markers = ["； 前文", "；前文", "; 前文", ";前文", "，前文", ", 前文", "； 后文", "；后文", "; 后文", ";后文", "，后文", ", 后文", "视觉摘要"];
  const cuts = markers
    .map((marker) => text.indexOf(marker))
    .filter((index) => index > 0);
  if (cuts.length) text = text.slice(0, Math.min(...cuts));
  text = text.replace(/\s*(前文|后文|视觉摘要)\s*[:：].*$/u, "").trim();
  text = text.replace(/[；;，,。]\s*$/u, "").trim();
  if (text.length > 72) {
    const punctuation = ["；", ";", "。", "，", ","]
      .map((token) => text.indexOf(token, 18))
      .filter((index) => index > 0);
    if (punctuation.length) text = text.slice(0, Math.min(...punctuation)).replace(/[；;，,。]\s*$/u, "").trim();
    if (text.length > 72) text = `${text.slice(0, 69).trim()}...`;
  }
  return text;
}

function AssistantMarkdownImage({ alt, src }: { alt: string; src: string }) {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const resolvedSrc = resolveMarkdownImageUrl(src);
  const protectedAsset = resolvedSrc.includes("/api/admin/rag-assets");
  const caption = cleanAssistantImageCaption(alt);

  useEffect(() => {
    if (!protectedAsset) {
      setImageSrc(resolvedSrc);
      setFailed(false);
      return;
    }

    const token = getAuthToken();
    const controller = new AbortController();
    let objectUrl: string | null = null;
    setImageSrc(null);
    setFailed(false);

    fetch(resolvedSrc, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setImageSrc(objectUrl);
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
  }, [protectedAsset, resolvedSrc]);

  if (failed) {
    return (
      <figure className="assistant-md-image assistant-md-image-failed">
        <div>图像资源暂时不可访问</div>
        {caption ? <figcaption title={alt}>{renderAssistantInlineMarkdown(caption)}</figcaption> : null}
      </figure>
    );
  }

  return (
    <figure className="assistant-md-image">
      {imageSrc ? (
        <img src={imageSrc} alt={caption || alt || "RAG 图像证据"} />
      ) : (
        <div className="assistant-md-image-loading" />
      )}
      {caption ? <figcaption title={alt}>{renderAssistantInlineMarkdown(caption)}</figcaption> : null}
    </figure>
  );
}

export function renderAssistantMarkdown(text: string | null | undefined): ReactNode {
  return <AssistantMarkdownContent text={text} />;
}
