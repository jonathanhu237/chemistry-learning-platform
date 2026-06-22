import { useCallback } from "react";
import { useCanGoBack, useNavigate } from "@tanstack/react-router";
import { fallbackRootPath } from "../router/routeVisibility";

export function useDetailBack(source?: string | null): () => void {
  const navigate = useNavigate();
  const canGoBack = useCanGoBack();
  return useCallback(() => {
    if (canGoBack) {
      window.history.back();
      return;
    }
    void navigate({ to: fallbackRootPath(source), replace: true });
  }, [canGoBack, navigate, source]);
}
