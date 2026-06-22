export function errorMessage(error: unknown) {
  if (error instanceof Error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (detail && typeof detail === "object") {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === "string" && message.trim()) return message;
    }
    return error.message;
  }
  return String(error || "请求失败");
}
