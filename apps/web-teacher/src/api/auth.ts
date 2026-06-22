export type User = {
  id: string;
  username: string;
  role: "platform_admin" | "admin" | "teacher" | "student";
  display_name: string;
  status: string;
  must_change_password?: boolean;
};

const ADMIN_TOKEN_STORAGE_KEY = "chem_web_teacher_token";

function getBrowserStorage(): Storage | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

function readStoredAuthToken(): string {
  try {
    return getBrowserStorage()?.getItem(ADMIN_TOKEN_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

function writeStoredAuthToken(token: string): void {
  try {
    const storage = getBrowserStorage();
    if (!storage) {
      return;
    }
    if (token) {
      storage.setItem(ADMIN_TOKEN_STORAGE_KEY, token);
    } else {
      storage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    }
  } catch {
    // Keep the in-memory token usable when storage is unavailable.
  }
}

let authToken = readStoredAuthToken();

export function getAuthToken(): string {
  return authToken;
}

export function setAuthToken(token: string): void {
  authToken = token;
  writeStoredAuthToken(token);
}

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};
