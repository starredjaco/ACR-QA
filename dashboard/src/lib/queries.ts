import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "./api";

export const useRuns = (limit = 20) =>
  useQuery({ queryKey: ["runs", limit], queryFn: () => api.getRuns(limit) });

export const useFindings = (runId: number, opts?: { params?: Record<string, string>; enabled?: boolean }) =>
  useQuery({
    queryKey: ["findings", runId, opts?.params],
    queryFn: () => api.getFindings(runId, opts?.params),
    enabled: opts?.enabled !== undefined ? opts.enabled : !!runId,
  });

export const useStats = (runId: number) =>
  useQuery({
    queryKey: ["stats", runId],
    queryFn: () => api.getStats(runId),
    enabled: !!runId,
  });

export const useCompliance = (runId: number) =>
  useQuery({
    queryKey: ["compliance", runId],
    queryFn: () => api.getCompliance(runId),
    enabled: !!runId,
  });

export const useAutofix = (runId: number, findingId: number, enabled: boolean) =>
  useQuery({
    queryKey: ["autofix", runId, findingId],
    queryFn: () => api.getAutofix(runId, findingId),
    enabled,
  });

export const useSupplyChain = (runId: number, opts?: { riskLevel?: string; enabled?: boolean }) =>
  useQuery({
    queryKey: ["supply-chain", runId, opts?.riskLevel],
    queryFn: () => api.getSupplyChain(runId, opts?.riskLevel),
    enabled: opts?.enabled !== undefined ? opts.enabled : !!runId,
  });

export const useTrends = () =>
  useQuery({ queryKey: ["trends"], queryFn: api.getTrends });

export const useSubmitScan = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ dir, repo }: { dir: string; repo: string }) =>
      api.submitScan(dir, repo),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["runs"] }),
  });
};
