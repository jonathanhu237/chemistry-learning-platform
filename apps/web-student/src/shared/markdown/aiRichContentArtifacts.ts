import { normalizeStudentMarkdown } from "./markdownNormalize";

export type AiRichContentKind = "table" | "mermaid";

export type ParsedMarkdownTable = {
  headers: string[];
  rows: string[][];
};

export type AiRichContentArtifact = {
  id: string;
  kind: AiRichContentKind;
  index: number;
  startLine: number;
  title: string;
  source: string;
  table?: ParsedMarkdownTable;
};

export type AiRichContentOpenContext = {
  historyId: string;
  messageId: string;
  onOpenArtifact: (artifact: AiRichContentArtifact) => void;
};

function safeIdPart(value: string): string {
  return value.replace(/[^a-zA-Z0-9_-]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "") || "artifact";
}

export function aiRichContentArtifactId(messageId: string, kind: AiRichContentKind, index: number): string {
  return `${safeIdPart(messageId)}-${kind}-${index}`;
}

function unescapeMarkdownCell(value: string): string {
  return value.trim().replace(/\\\|/g, "|");
}

function splitTableRow(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  const cells: string[] = [];
  let current = "";
  let escaped = false;
  for (const char of trimmed) {
    if (escaped) {
      current += char;
      escaped = false;
      continue;
    }
    if (char === "\\") {
      current += char;
      escaped = true;
      continue;
    }
    if (char === "|") {
      cells.push(unescapeMarkdownCell(current));
      current = "";
      continue;
    }
    current += char;
  }
  cells.push(unescapeMarkdownCell(current));
  return cells;
}

function isSeparatorRow(line: string): boolean {
  const cells = splitTableRow(line);
  return cells.length > 1 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function looksLikeTableRow(line: string): boolean {
  const trimmed = line.trim();
  if (!trimmed || !trimmed.includes("|")) return false;
  return splitTableRow(trimmed).length > 1;
}

function normalizeRow(cells: string[], targetLength: number): string[] {
  if (cells.length === targetLength) return cells;
  if (cells.length > targetLength) return cells.slice(0, targetLength);
  return [...cells, ...Array.from({ length: targetLength - cells.length }, () => "")];
}

export function parseMarkdownTable(source: string): ParsedMarkdownTable | null {
  const lines = source
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2 || !isSeparatorRow(lines[1])) return null;
  const headers = splitTableRow(lines[0]);
  if (!headers.length) return null;
  const rows = lines.slice(2).filter(looksLikeTableRow).map((line) => normalizeRow(splitTableRow(line), headers.length));
  return { headers, rows };
}

function titleForArtifact(kind: AiRichContentKind, index: number, table?: ParsedMarkdownTable): string {
  if (kind === "mermaid") return `流程图 ${index}`;
  const firstHeader = table?.headers.find((header) => header.trim());
  return firstHeader ? `表格 ${index}: ${firstHeader}` : `表格 ${index}`;
}

export function extractAiRichContentArtifacts(markdown: string, messageId: string): AiRichContentArtifact[] {
  const value = normalizeStudentMarkdown(markdown);
  const lines = value.split(/\r?\n/);
  const artifacts: AiRichContentArtifact[] = [];
  let tableIndex = 0;
  let mermaidIndex = 0;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index] || "";
    const fenceMatch = line.trim().match(/^(`{3,}|~{3,})\s*mermaid\b/i);
    if (fenceMatch) {
      const startLine = index + 1;
      const fence = fenceMatch[1];
      const fenceChar = fence[0];
      const fenceLength = fence.length;
      const content: string[] = [];
      index += 1;
      while (index < lines.length) {
        const candidate = lines[index] || "";
        const closeMatch = candidate.trim().match(/^(`{3,}|~{3,})\s*$/);
        if (closeMatch && closeMatch[1][0] === fenceChar && closeMatch[1].length >= fenceLength) break;
        content.push(candidate);
        index += 1;
      }
      const source = content.join("\n").trim();
      if (source) {
        mermaidIndex += 1;
        artifacts.push({
          id: aiRichContentArtifactId(messageId, "mermaid", mermaidIndex),
          kind: "mermaid",
          index: mermaidIndex,
          startLine,
          title: titleForArtifact("mermaid", mermaidIndex),
          source,
        });
      }
      continue;
    }

    if (index + 1 < lines.length && looksLikeTableRow(line) && isSeparatorRow(lines[index + 1] || "")) {
      const startLine = index + 1;
      const tableLines = [line, lines[index + 1] || ""];
      index += 2;
      while (index < lines.length && looksLikeTableRow(lines[index] || "")) {
        tableLines.push(lines[index] || "");
        index += 1;
      }
      index -= 1;
      const source = tableLines.join("\n");
      const table = parseMarkdownTable(source);
      if (table) {
        tableIndex += 1;
        artifacts.push({
          id: aiRichContentArtifactId(messageId, "table", tableIndex),
          kind: "table",
          index: tableIndex,
          startLine,
          title: titleForArtifact("table", tableIndex, table),
          source,
          table,
        });
      }
    }
  }

  return artifacts;
}

export function findAiRichContentArtifact(markdown: string, messageId: string, artifactId: string): AiRichContentArtifact | null {
  return extractAiRichContentArtifacts(markdown, messageId).find((artifact) => artifact.id === artifactId) || null;
}
