import { Suspense, lazy } from "react";

const LazyAiMarkdown = lazy(async () => {
  const module = await import("../../components/AiMarkdown");
  return { default: module.AiMarkdown };
});

export function AiMarkdownBlock({ text, className = "" }: { text: string | null | undefined; className?: string }) {
  const value = String(text || "");
  if (!value.trim()) return null;
  return (
    <Suspense
      fallback={
        <div className={["ai-markdown", className].filter(Boolean).join(" ")}>
          <p className="ai-md-paragraph">{value}</p>
        </div>
      }
    >
      <LazyAiMarkdown text={value} className={className} />
    </Suspense>
  );
}
