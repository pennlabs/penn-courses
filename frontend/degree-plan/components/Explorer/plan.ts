import type { Fulfillment } from "@/types";
import { ruleNodeId, type LeafCourse } from "./graph";
import { findMatches, fulfillmentCourse, type Match, type MatchableCourse } from "./matcher";
import type { Program } from "./programs";

/** One course in a degree plan, with every bucket it could fill across the plan's programs. */
export interface PlanCourse {
  fulfillment: Fulfillment;
  course: MatchableCourse;
  matches: Match[];
  /** The programs those buckets are in, in program order. Two or more is a double count. */
  programs: Program[];
}

export const toPlanCourses = (programs: Program[], fulfillments: Fulfillment[]): PlanCourse[] =>
  fulfillments.map((fulfillment) => {
    const course = fulfillmentCourse(fulfillment);
    const matches = findMatches(programs, course);
    return {
      fulfillment,
      course,
      matches,
      programs: programs.filter((program) => matches.some((m) => m.program === program)),
    };
  });

/** Leaf node id → the plan's courses that could fill that leaf. */
export const leafCourses = (planCourses: PlanCourse[]): Map<string, LeafCourse[]> => {
  const byLeaf = new Map<string, LeafCourse[]>();
  planCourses.forEach(({ fulfillment, matches }) => {
    matches.forEach(({ program, leaf }) => {
      const id = ruleNodeId(program, leaf);
      const placed = fulfillment.rules.includes(leaf.id);
      byLeaf.set(id, [...(byLeaf.get(id) ?? []), { fullCode: fulfillment.full_code, placed }]);
    });
  });
  return byLeaf;
};
