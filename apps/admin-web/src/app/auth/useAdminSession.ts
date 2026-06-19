import { useQuery } from "@tanstack/react-query";

import { api } from "../../api";
import type { User } from "../../api";

export function useAdminSession(token: string) {
  return useQuery({
    queryKey: ["me", token],
    queryFn: () => api<User>("/api/auth/me"),
    enabled: Boolean(token),
    retry: false,
  });
}
