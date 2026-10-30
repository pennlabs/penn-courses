import type { Rule } from "@/types";
import { isLeaf } from "./graph";
import { courseMatches, type MatchableCourse } from "./matcher";
import type { Program } from "./programs";

export interface Disagreement {
  rule: Rule;
  ours: boolean;
  backend: boolean;
}

export interface VerifyResult {
  checked: number;
  disagreements: Disagreement[];
}

/** Each leaf with a q across the programs, once each (rules are shared between programs). */
const uniqueLeaves = (programs: Program[]): Rule[] => {
  const leaves = new Map<number, Rule>();
  const visit = (rule: Rule) => {
    if (!isLeaf(rule)) rule.rules.forEach(visit);
    else if (rule.q_json) leaves.set(rule.id, rule);
  };
  programs.forEach((program) => program.rules.forEach(visit));
  return Array.from(leaves.values());
};

// The rule_ids filter runs the backend's own Q for the rule (courses/filters.py).
const backendMatches = async (fullCode: string, ruleId: number): Promise<boolean> => {
  const url = `/api/base/all/search/courses?search=${fullCode}&rule_ids=${ruleId}&page_size=50`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request to ${url} failed with status ${res.status}`);
  const data = await res.json();
  const results: { id: string }[] = data.results ?? data;
  return results.some((course) => course.id === fullCode);
};

const BATCH_SIZE = 6;

/**
 * Asks the backend whether the course belongs to each leaf and compares with the matcher.
 * One request per leaf, a few at a time, so this is a debugging aid rather than a live view.
 */
export const verifyAgainstBackend = async (
  programs: Program[],
  course: MatchableCourse,
  onProgress: (done: number, total: number) => void
): Promise<VerifyResult> => {
  const leaves = uniqueLeaves(programs);
  const disagreements: Disagreement[] = [];
  for (let i = 0; i < leaves.length; i += BATCH_SIZE) {
    const batch = leaves.slice(i, i + BATCH_SIZE);
    const answers = await Promise.all(batch.map((rule) => backendMatches(course.full_code, rule.id)));
    batch.forEach((rule, j) => {
      const ours = courseMatches(rule.q_json, course);
      if (ours !== answers[j]) disagreements.push({ rule, ours, backend: answers[j] });
    });
    onProgress(Math.min(i + BATCH_SIZE, leaves.length), leaves.length);
  }
  return { checked: leaves.length, disagreements };
};
