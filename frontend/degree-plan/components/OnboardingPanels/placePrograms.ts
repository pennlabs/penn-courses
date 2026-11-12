import { DegreeListing, DegreePlan, DualProgram } from "@/types";
import { deleteFetcher, postFetcher } from "@/hooks/swrcrud";

// Attaches a coordinated program to a plan whose degrees already include both sides, or detaches
// the plan's program when `program` is undefined.
export const setDualProgram = async (
  planId: DegreePlan["id"],
  program: DualProgram | undefined,
  sides: { left?: DegreeListing; right?: DegreeListing }
) => {
  const url = `/api/degree/degreeplans/${planId}/dual-program`;
  if (!program) {
    await deleteFetcher(url);
    return;
  }
  await postFetcher(url, {
    code: program.code,
    left_id: sides.left?.id,
    right_id: sides.right?.id,
  });
};

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
