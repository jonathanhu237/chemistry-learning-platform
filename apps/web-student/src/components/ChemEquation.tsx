import { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import "katex/contrib/mhchem";

function renderKatex(latex: string, displayMode: boolean): string {
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

export function ChemEquation({
  latex,
  fallback,
  displayMode = false,
  className = "",
}: {
  latex: string | null;
  fallback: string;
  displayMode?: boolean;
  className?: string;
}) {
  const html = useMemo(() => (latex ? renderKatex(latex, displayMode) : ""), [displayMode, latex]);
  if (!html) return <code className={["chem-equation-fallback", className].filter(Boolean).join(" ")}>{fallback}</code>;
  return (
    <span
      className={["chem-equation", displayMode ? "chem-equation-display" : "chem-equation-inline", className].filter(Boolean).join(" ")}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
