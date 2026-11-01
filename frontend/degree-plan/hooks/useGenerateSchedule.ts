import { useEffect, useRef, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { Fulfillment, GenerateResponse } from "@/types";
import { postFetcher } from "@/hooks/swrcrud";
import { isCurrentRequest, nextRequestId, publishProposal, StoredGenConfig } from "@/hooks/generateConfig";

/**
 * Debounced, stale-guarded call to POST /generate. Nothing is requested until the plan and
 * its semesters are known.
 * Fulfillment changes and semester-config changes both retrigger it.
 */
export function useGenerateSchedule(
  planId: number | null | undefined,
  config: StoredGenConfig | null,
  semesterKeys: string[],
) {
  const { data: fulfillments } = useSWR<Fulfillment[]>(
    planId ? `/api/degree/degreeplans/${planId}/fulfillments` : null
  );
  const [proposal, setProposal] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const latest = useRef(0);
  const skipFulfillmentRefresh = useRef(false);
  const { mutate } = useSWRConfig();

  const enabled = Boolean(config && planId && semesterKeys.length);

  useEffect(() => {
    if (skipFulfillmentRefresh.current) {
      skipFulfillmentRefresh.current = false;
      return undefined;
    }
    if (!enabled || !planId || !config) {
      setProposal(null);
      publishProposal(null);
      return undefined;
    }
    const id = nextRequestId();
    latest.current = id;
    const handle = window.setTimeout(async () => {
      try {
        const body = {
          allow_summer: config.allowSummer,
          pinned_slots: Object.entries(config.pinnedSlots || {}).map(([slot_id, semester]) => ({
            slot_id,
            semester,
          })),
          semesters: semesterKeys
            .filter((key) => /^\d{4}[ABC]$/.test(key))
            .map((key) => ({
              key,
              cu_cap: config.semesters[key]?.cuCap,
              gap: Boolean(config.semesters[key]?.gap),
            })),
        };
        const data = await postFetcher(`/api/degree/degreeplans/${planId}/generate`, body) as GenerateResponse;
        if (isCurrentRequest(id, latest.current)) {
          setProposal(data);
          publishProposal(data);
          setError(null);
          if (data.claims_updated) {
            skipFulfillmentRefresh.current = true;
            mutate(`/api/degree/degreeplans/${planId}/fulfillments`);
            mutate(`/api/degree/degreeplans/${planId}/summary`);
          }
        }
      } catch (err) {
        if (isCurrentRequest(id, latest.current)) {
          setProposal(null);
          setError("Schedule unavailable");
        }
      }
    }, 500);
    return () => window.clearTimeout(handle);
    // fulfillments is the signal that the editor changed; the hook refetches when SWR does.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, planId, config, semesterKeys.join("|"), fulfillments]);

  return { proposal, error, enabled };
}
