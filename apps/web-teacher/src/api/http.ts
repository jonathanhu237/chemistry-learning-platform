import { getAuthToken, setAuthToken } from "./auth";

export const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const authToken = getAuthToken();
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (response.status === 401) {
    setAuthToken("");
  }
  if (!response.ok) {
    throw new ApiError(response.status, typeof payload === "object" && payload ? payload.detail : payload);
  }
  return payload as T;
}

export type JsonStreamEvent<T = unknown> = {
  event: string;
  data: T;
};

function parseSseBlock(raw: string): JsonStreamEvent | null {
  const lines = raw.split(/\r?\n/);
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim() || "message";
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }
  if (!dataLines.length) return null;
  const dataText = dataLines.join("\n");
  try {
    return { event, data: JSON.parse(dataText) };
  } catch {
    return { event, data: dataText };
  }
}

export async function postJsonStream<T>(
  path: string,
  body: unknown,
  onEvent: (event: JsonStreamEvent<T>) => void | Promise<void>,
): Promise<void> {
  const headers = new Headers();
  headers.set("Accept", "text/event-stream");
  headers.set("Content-Type", "application/json");
  const authToken = getAuthToken();
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const response = await fetch(`${apiBase}${path}`, { method: "POST", body: JSON.stringify(body), headers });
  if (response.status === 401) {
    setAuthToken("");
  }
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    throw new ApiError(response.status, typeof payload === "object" && payload ? payload.detail : payload);
  }
  if (!response.body) {
    throw new ApiError(response.status, "当前浏览器不支持流式响应读取");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const event = parseSseBlock(block);
      if (event) await onEvent(event as JsonStreamEvent<T>);
    }
    if (done) break;
  }

  const event = parseSseBlock(buffer);
  if (event) await onEvent(event as JsonStreamEvent<T>);
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function patchJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export function putJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PUT", body: JSON.stringify(body) });
}
