import { DegreePlan, Rule } from "@/types";

export type ProgramKind = "degree" | "major" | "minor";

export interface PlanProgram {
  id: number;
  relation: "degrees" | "majors" | "minors";
  kind: ProgramKind;
  title: string;
  code: string; // a short label, for when the full title doesn't fit
  year: number;
  rules: Rule[];
}

export const planPrograms = (detail: DegreePlan): PlanProgram[] => [
  ...(detail.degrees ?? []).map((degree) => ({
    id: degree.id,
    relation: "degrees" as const,
    kind: "degree" as const,
    title: `${degree.degree} in ${degree.major_name}${
      degree.concentration ? ` (${degree.concentration_name})` : ""
    }`,
    code: `${degree.degree} ${degree.major}`,
    year: degree.year,
    rules: degree.rules,
  })),
  ...(detail.majors ?? []).map((major) => ({
    id: major.id,
    relation: "majors" as const,
    kind: "major" as const,
    title: `Major in ${major.name}${
      major.concentration_name ? ` (${major.concentration_name})` : ""
    }`,
    code: major.code,
    year: major.year,
    rules: major.rules,
  })),
  ...(detail.minors ?? []).map((minor) => ({
    id: minor.id,
    relation: "minors" as const,
    kind: "minor" as const,
    title: `Minor in ${minor.name}`,
    code: minor.code,
    year: minor.year,
    rules: minor.rules,
  })),
];

export interface RuleInProgram {
  title: string;
  program: PlanProgram;
}

/** Every rule of a plan, nested ones included, with the program it belongs to. */
export const rulesByProgram = (
  detail: DegreePlan
): Map<number, RuleInProgram> => {
  const map = new Map<number, RuleInProgram>();
  const visit = (rules: Rule[], program: PlanProgram) => {
    for (const rule of rules) {
      if (!map.has(rule.id)) map.set(rule.id, { title: rule.title, program });
      if (rule.rules?.length) visit(rule.rules, program);
    }
  };
  for (const program of planPrograms(detail)) visit(program.rules, program);
  return map;
};
