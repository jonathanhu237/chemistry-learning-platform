import type { StoredPosttestReport, StoredPosttestSession } from "./routeTypes";

const sessionPrefix = "student-posttest-session:";
const reportPrefix = "student-posttest-report:";

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

function readJson<T>(key: string): T | null {
  const raw = storage()?.getItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function storePosttestSession(posttest: StoredPosttestSession): void {
  storage()?.setItem(`${sessionPrefix}${posttest.session_id}`, JSON.stringify(posttest));
}

export function loadPosttestSession(sessionId: string): StoredPosttestSession | null {
  return readJson<StoredPosttestSession>(`${sessionPrefix}${sessionId}`);
}

export function storePosttestReport(report: StoredPosttestReport): void {
  storage()?.setItem(`${reportPrefix}${report.session_id}`, JSON.stringify(report));
}

export function loadPosttestReport(sessionId: string): StoredPosttestReport | null {
  return readJson<StoredPosttestReport>(`${reportPrefix}${sessionId}`);
}
