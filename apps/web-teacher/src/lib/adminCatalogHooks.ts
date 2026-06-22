import { useQuery } from "@tanstack/react-query";

import type { ApiList } from "../api/common";
import type { Experiment } from "../api/experiments";
import { listExperiments } from "../api/experiments";
import type { Chapter } from "../api/resources";
import { listChapters } from "../api/resources";

export function useAdminChapters() {
  return useQuery({ queryKey: ["chapters"], queryFn: listChapters });
}

export function useAdminExperiments(params = "") {
  return useQuery<ApiList<Experiment>>({
    queryKey: ["admin-experiments", params],
    queryFn: () => listExperiments(params),
  });
}
