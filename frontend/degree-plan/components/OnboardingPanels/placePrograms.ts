import { DegreePlan } from "@/types";
import { postFetcher } from "@/hooks/swrcrud";

export type Placement = {
  degreeId: number | undefined;
  majorIds: number[];
  minorIds: number[];
};

// Adds majors and minors to a plan under the degree each belongs to. The degrees must already be
// on the plan for `degree_id` to be accepted.
export const placePrograms = async (
  planId: DegreePlan["id"],
  placements: Placement[]
) => {
  const base = `/api/degree/degreeplans/${planId}`;
  // Each post reallocates the whole plan, so they must not overlap.
  for (const { degreeId, majorIds, minorIds } of placements) {
    if (majorIds.length)
      // eslint-disable-next-line no-await-in-loop
      await postFetcher(`${base}/majors`, {
        major_ids: majorIds,
        degree_id: degreeId,
      });
    if (minorIds.length)
      // eslint-disable-next-line no-await-in-loop
      await postFetcher(`${base}/minors`, {
        minor_ids: minorIds,
        degree_id: degreeId,
      });
  }
};
