export function stripExperimentPrefix(value: string): string {
  return value.replace(/^实验\s+\d+(?:-\d+)?\s*/, "").trim() || value;
}
