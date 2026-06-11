import { useQuery } from "@tanstack/react-query";
import { resourcesApi } from "@/services/api/resources";

export function useResources() {
  return useQuery({
    queryKey: ["resources"],
    queryFn: () => resourcesApi.list({ limit: 100 }),
    staleTime: 60_000,
  });
}
