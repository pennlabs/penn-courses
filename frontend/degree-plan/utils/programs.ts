import { DegreePlan, Rule } from "@/types";

// Some catalog years record a program without a concentration as Path's "No Concentration" or
// "Non Designated", where others leave it empty.
export const NO_CONCENTRATION_CODES = ["NCON", "NONE"];
export const hasConcentration = (code: string | null | undefined) =>
  !!code && !NO_CONCENTRATION_CODES.includes(code);

// What stays the same across the catalog years of a degree, as the backend matches them.
export const degreeProgramOf = (degree: {
  program: string;
  degree: string;
  major: string;
  concentration: string | null;
}) =>
  [
    degree.program,
    degree.degree,
    degree.major,
    hasConcentration(degree.concentration) ? degree.concentration : null,
  ].join("|");

// What stays the same across the catalog years of a major or minor, e.g. CSCI-BA for CSCI-BA-NCON.
const NO_CONCENTRATION_SUFFIX = new RegExp(`-(${NO_CONCENTRATION_CODES.join("|")})$`);
export const programCodeOf = (program: { program_code: string }) =>
  program.program_code.replace(NO_CONCENTRATION_SUFFIX, "");

// Who each of a program's versions is for, by the fall students started in: a version applies
// until the next one does, e.g. "Fall 2024–2025" then "Fall 2026 or later".
export const startingYearsLabels = (catalogYears: number[]) =>
  catalogYears.map((year, i) => {
    const first = year - 1;
    const next = catalogYears[i + 1];
    if (next === undefined) return `Fall ${first} or later`;
    const last = next - 2;
    return last > first ? `Fall ${first}–${last}` : `Fall ${first}`;
  });

// Pre-med, which a plan holds as a major though it isn't a Penn program.
export const PREMED_PROGRAM_CODE = "PREMED";
export const isPremed = (program: { program_code?: string }) =>
  program.program_code === PREMED_PROGRAM_CODE;

export type ProgramKind = "degree" | "major" | "minor";

export interface PlanProgram {
  id: number;
  relation: "degrees" | "majors" | "minors";
  kind: ProgramKind;
  title: string;
  code: string; // a short label, for when the full title doesn't fit
  family: string; // the same across the program's catalog years
  year: number;
  catalogYears: { id: number; year: number }[]; // this program's versions, this one included
  rules: Rule[];
}

// A coordinated program (e.g. M&T) adds requirements to a degree and drops others. The plan's
// components carry each degree's requirements with those changes made.
const withProgramChanges = (
  detail: DegreePlan,
  programs: PlanProgram[]
): PlanProgram[] => {
  if (!detail.dual_program || !detail.components) return programs;
  return programs.map((program) => {
    const component = detail.components!.find(
      (c) => c.relation === program.relation && c.id === program.id
    );
    return component ? { ...program, rules: component.rules } : program;
  });
};

const catalogYearsOf = (
  detail: DegreePlan,
  relation: PlanProgram["relation"],
  program: { id: number; year: number }
) =>
  detail.catalog_years?.[relation]?.[program.id] ?? [
    { id: program.id, year: program.year },
  ];

export const planPrograms = (detail: DegreePlan): PlanProgram[] =>
  withProgramChanges(detail, [
    ...(detail.degrees ?? []).map((degree) => ({
      id: degree.id,
      relation: "degrees" as const,
      kind: "degree" as const,
      title: `${degree.degree} in ${degree.major_name}${
        hasConcentration(degree.concentration)
          ? ` (${degree.concentration_name})`
          : ""
      }`,
      code: `${degree.degree} ${degree.major}`,
      family: degreeProgramOf(degree),
      year: degree.year,
      catalogYears: catalogYearsOf(detail, "degrees", degree),
      rules: degree.rules,
    })),
    ...(detail.majors ?? []).map((major) => ({
      id: major.id,
      relation: "majors" as const,
      kind: "major" as const,
      title: isPremed(major) ? major.name ?? "Pre-Medicine" : `Major in ${major.name}${
        major.concentration_name && hasConcentration(major.concentration)
          ? ` (${major.concentration_name})`
          : ""
      }`,
      code: major.code,
      family: programCodeOf(major),
      year: major.year,
      catalogYears: catalogYearsOf(detail, "majors", major),
      rules: major.rules,
    })),
    ...(detail.minors ?? []).map((minor) => ({
      id: minor.id,
      relation: "minors" as const,
      kind: "minor" as const,
      title: `Minor in ${minor.name}`,
      code: minor.code,
      family: programCodeOf(minor),
      year: minor.year,
      catalogYears: catalogYearsOf(detail, "minors", minor),
      rules: minor.rules,
    })),
  ]);

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
