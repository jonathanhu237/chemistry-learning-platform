import { useQuery } from "@tanstack/react-query";

import type { User } from "../../api/auth";
import { api } from "../../api/http";

export function useAdminSession(token: string) {
  return useQuery({
    queryKey: ["me", token],
    queryFn: () => api<User>("/api/auth/me"),
    enabled: Boolean(token),
    retry: false,
  });
}
