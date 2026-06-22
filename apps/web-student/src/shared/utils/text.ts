export function compactText(parts: Array<string | null | undefined>): string {
  return parts
    .map((part) => String(part || "").trim())
    .filter(Boolean)
    .join("；")
    .slice(0, 1800);
}
