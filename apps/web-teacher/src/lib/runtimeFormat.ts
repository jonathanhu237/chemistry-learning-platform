function traceNumber(value: unknown): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function formatTraceMs(value: unknown): string {
  const numberValue = traceNumber(value);
  if (numberValue === undefined) return "-";
  return numberValue >= 1000 ? `${(numberValue / 1000).toFixed(2)} s` : `${numberValue.toFixed(0)} ms`;
}

export function formatRuntimeSeconds(value: unknown): string {
  const numberValue = traceNumber(value);
  if (numberValue === undefined) return "-";
  if (numberValue >= 3600) return `${(numberValue / 3600).toFixed(1)} h`;
  if (numberValue >= 60) return `${(numberValue / 60).toFixed(1)} min`;
  return `${numberValue.toFixed(0)} s`;
}

export function formatMemoryMb(value: unknown): string {
  const numberValue = traceNumber(value);
  return numberValue === undefined ? "-" : `${numberValue.toFixed(1)} MB`;
}

export function warmupStatusLabel(status?: string) {
  const labels: Record<string, string> = {
    disabled: "未启用预热",
    not_started: "未预热",
    running: "预热中",
    succeeded: "已就绪",
    failed: "预热失败",
  };
  return labels[String(status || "")] || String(status || "未知");
}
