export function previewBackOrClose(): void {
  if (typeof window === "undefined") return;
  if (window.history.length > 1) {
    window.history.back();
    return;
  }
  try {
    window.parent?.postMessage({ type: "catalog-preview-close" }, "*");
  } catch {
    // Cross-origin parent access can fail in embedded preview shells.
  }
  window.close();
}
