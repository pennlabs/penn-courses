import { PrereqRule } from "@/types";

/**
 * Whether `rule` is met by the courses in `taken`. A condition that isn't a course (e.g.
 * instructor permission) can't be checked, so it counts as met.
 */
export const isPrereqRuleMet = (
  rule: PrereqRule,
  taken: Set<string>
): boolean => {
  if (typeof rule === "string") return taken.has(rule);
  if ("and" in rule)
    return rule.and.every((child) => isPrereqRuleMet(child, taken));
  if ("or" in rule)
    return rule.or.some((child) => isPrereqRuleMet(child, taken));
  return true;
};

/** A rule as text, e.g. "CIS 1200 and (CIS 1600 or MATH 1400)". */
export const formatPrereqRule = (rule: PrereqRule, nested = false): string => {
  if (typeof rule === "string") return rule.replace("-", " ");
  if ("text" in rule) return rule.text;
  const [op, children] = "and" in rule ? ["and", rule.and] : ["or", rule.or];
  const text = children
    .map((child) => formatPrereqRule(child, true))
    .join(` ${op} `);
  return nested ? `(${text})` : text;
};

/**
 * The parts of `rule` not met by `taken`, formatted for display: each unmet requirement of a
 * top-level "and", or the whole rule otherwise. Empty when the rule is met.
 */
export const unmetPrereqs = (
  rule: PrereqRule,
  taken: Set<string>
): string[] => {
  if (isPrereqRuleMet(rule, taken)) return [];
  const parts = typeof rule !== "string" && "and" in rule ? rule.and : [rule];
  return parts
    .filter((part) => !isPrereqRuleMet(part, taken))
    .map((part) => formatPrereqRule(part));
};
