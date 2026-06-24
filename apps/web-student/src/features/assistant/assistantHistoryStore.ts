import type { AgentChatMessage, StudentAssistantFinalMetadata } from "../../api";
import type { AssistantContext } from "./assistantContext";

const STORAGE_KEY = "student-ai-chat-history:v1";
const MAX_HISTORY_ENTRIES = 30;
const MAX_STORED_MESSAGES = 40;

export type StudentAiChatMessage = AgentChatMessage & {
  metadata?: StudentAssistantFinalMetadata;
  state?: "error";
};

export type StudentAiHistorySource = "root" | "detail";

export type StudentAiHistoryEntry = {
  id: string;
  title: string;
  contextTitle: string;
  contextType: AssistantContext["context_type"];
  contextSummary: string;
  source: StudentAiHistorySource;
  context: AssistantContext;
  messages: StudentAiChatMessage[];
  createdAt: string;
  updatedAt: string;
};

function storage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function nowIso(): string {
  return new Date().toISOString();
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function messagesFrom(value: unknown): StudentAiChatMessage[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((message): message is StudentAiChatMessage => {
      if (!message || typeof message !== "object") return false;
      const role = (message as StudentAiChatMessage).role;
      return (role === "user" || role === "assistant") && typeof (message as StudentAiChatMessage).content === "string";
    })
    .slice(-MAX_STORED_MESSAGES);
}

function contextFrom(value: unknown): AssistantContext | null {
  if (!value || typeof value !== "object") return null;
  const context = value as AssistantContext;
  if (!context.context_type || !context.context_title) return null;
  return {
    ...context,
    context_summary: text(context.context_summary),
    prompts: Array.isArray(context.prompts) ? context.prompts.filter((prompt): prompt is string => typeof prompt === "string") : [],
  };
}

function normalizeEntry(value: unknown): StudentAiHistoryEntry | null {
  if (!value || typeof value !== "object") return null;
  const entry = value as StudentAiHistoryEntry;
  const context = contextFrom(entry.context);
  const messages = messagesFrom(entry.messages);
  if (!entry.id || !context || !messages.length) return null;
  return {
    id: text(entry.id),
    title: text(entry.title) || historyTitleFromMessages(messages),
    contextTitle: text(entry.contextTitle) || context.context_title,
    contextType: context.context_type,
    contextSummary: text(entry.contextSummary) || text(context.context_summary),
    source: entry.source === "detail" ? "detail" : "root",
    context,
    messages,
    createdAt: text(entry.createdAt) || nowIso(),
    updatedAt: text(entry.updatedAt) || nowIso(),
  };
}

function readAll(): StudentAiHistoryEntry[] {
  const local = storage();
  if (!local) return [];
  try {
    const parsed = JSON.parse(local.getItem(STORAGE_KEY) || "[]") as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map(normalizeEntry)
      .filter((entry): entry is StudentAiHistoryEntry => Boolean(entry))
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
      .slice(0, MAX_HISTORY_ENTRIES);
  } catch {
    return [];
  }
}

function writeAll(entries: StudentAiHistoryEntry[]): void {
  const local = storage();
  if (!local) return;
  try {
    local.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_HISTORY_ENTRIES)));
  } catch {
    // Local history is a convenience layer; quota/private-mode failures should not block chat.
  }
}

export function createStudentAiHistoryId(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") return globalThis.crypto.randomUUID();
  return `student-ai-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function historyTitleFromMessages(messages: StudentAiChatMessage[]): string {
  const firstQuestion = messages.find((message) => message.role === "user" && message.content.trim())?.content.trim();
  if (!firstQuestion) return "新的 Atom 对话";
  const compact = firstQuestion.replace(/\s+/g, " ");
  return compact.length > 28 ? `${compact.slice(0, 28)}...` : compact;
}

export function buildStudentAiHistoryEntry({
  id,
  context,
  messages,
  source,
  createdAt,
}: {
  id: string;
  context: AssistantContext;
  messages: StudentAiChatMessage[];
  source: StudentAiHistorySource;
  createdAt?: string;
}): StudentAiHistoryEntry {
  const timestamp = nowIso();
  return {
    id,
    title: historyTitleFromMessages(messages),
    contextTitle: context.context_title,
    contextType: context.context_type,
    contextSummary: context.context_summary,
    source,
    context,
    messages: messagesFrom(messages),
    createdAt: createdAt || timestamp,
    updatedAt: timestamp,
  };
}

export function listStudentAiHistory(): StudentAiHistoryEntry[] {
  return readAll();
}

export function readStudentAiHistory(id: string): StudentAiHistoryEntry | null {
  return readAll().find((entry) => entry.id === id) || null;
}

export function upsertStudentAiHistory(entry: StudentAiHistoryEntry): StudentAiHistoryEntry {
  const normalized = normalizeEntry(entry) || entry;
  const entries = [normalized, ...readAll().filter((item) => item.id !== normalized.id)].slice(0, MAX_HISTORY_ENTRIES);
  writeAll(entries);
  return normalized;
}

export function deleteStudentAiHistory(id: string): void {
  writeAll(readAll().filter((entry) => entry.id !== id));
}

export function clearStudentAiHistory(): void {
  writeAll([]);
}
