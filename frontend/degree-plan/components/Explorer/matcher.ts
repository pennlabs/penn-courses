import type { Fulfillment, Rule } from "@/types";
import { isLeaf, ruleNodeId } from "./graph";
import type { Program } from "./programs";
import type { QJson } from "./qToText";

/** The parts of a course a rule's q can look at. */
export interface MatchableCourse {
  full_code: string;
  department: string;
  /** The number part of the code, e.g. "1200". A string, like the backend's Course.code. */
  code: string;
  semester: string;
  attributes: string[];
}

/** What `/api/base/all/courses/<code>` returns that the matcher needs. */
export interface CourseDetail {
  id: string;
  title: string;
  semester: string;
  attributes: { code: string }[];
}

const matchableCourse = (
  fullCode: string,
  semester: string,
  attributes: string[]
): MatchableCourse => {
  const [department, code] = fullCode.split("-");
  return { full_code: fullCode, department, code, semester, attributes };
};

export const toMatchableCourse = (course: CourseDetail): MatchableCourse =>
  matchableCourse(course.id, course.semester, course.attributes.map((a) => a.code));

/**
 * A plan's course, using the catalog course the backend attached to it. A course missing from
 * the catalog has no attributes, so only rules that name it can match it.
 */
export const fulfillmentCourse = (fulfillment: Fulfillment): MatchableCourse =>
  matchableCourse(
    fulfillment.full_code,
    fulfillment.course?.semester ?? fulfillment.semester ?? "",
    fulfillment.course?.attribute_codes ?? []
  );

/** "cis 1200" or "CIS1200" → "CIS-1200". */
export const normalizeFullCode = (input: string) =>
  input
    .trim()
    .toUpperCase()
    .replace(/^([A-Z]+)[\s-]*(\d)/, "$1-$2");

const asList = (value: unknown) => (Array.isArray(value) ? value.map(String) : [String(value)]);

// Codes and semesters are compared as strings, as the database compares the CharFields.
const compare = (field: string, lookup: string | undefined, value: unknown): boolean => {
  const v = String(value);
  switch (lookup) {
    case undefined:
    case "exact":
      return field === v;
    case "in":
      return asList(value).includes(field);
    case "gte":
      return field >= v;
    case "lte":
      return field <= v;
    case "gt":
      return field > v;
    case "lt":
      return field < v;
    case "startswith":
      return field.startsWith(v);
    default:
      return false;
  }
};

const FIELDS: Record<string, (course: MatchableCourse) => string> = {
  full_code: (c) => c.full_code,
  department__code: (c) => c.department,
  code: (c) => c.code,
  semester: (c) => c.semester,
};

// Keys the matcher doesn't know, so a leaf that uses one never matches. Logged once each.
const warned = new Set<string>();

const leafMatches = (key: string, value: unknown, course: MatchableCourse): boolean => {
  if (key === "attributes__code__in" || key === "attributes__code") {
    const wanted = asList(value);
    return course.attributes.some((code) => wanted.includes(code));
  }
  const field = Object.keys(FIELDS).find((f) => key === f || key.startsWith(`${f}__`));
  const lookup = field && key.slice(field.length + 2);
  if (field && (lookup === "" || ["exact", "in", "gte", "lte", "gt", "lt", "startswith"].includes(lookup!))) {
    return compare(FIELDS[field](course), lookup || undefined, value);
  }
  if (!warned.has(key)) {
    warned.add(key);
    console.warn(`Explorer matcher: unsupported q key "${key}"`);
  }
  return false;
};

/**
 * Whether a course satisfies a rule's q_json, mirroring the Django filter the backend runs
 * (Rule.check_belongs). Empty AND/OR clauses match everything, as an empty Q() does.
 */
export const courseMatches = (q: QJson, course: MatchableCourse): boolean => {
  switch (q.type) {
    case "COURSE":
      return course.full_code === q.full_code;
    case "LEAF":
      return leafMatches(q.key, q.value, course);
    case "NOT":
      return !courseMatches(q.clauses[0], course);
    case "AND":
      return q.clauses.every((clause) => courseMatches(clause, course));
    case "OR":
      return q.clauses.length === 0 || q.clauses.some((clause) => courseMatches(clause, course));
    default:
      return false;
  }
};

export interface Match {
  program: Program;
  leaf: Rule;
  /** Rules from the program's top level down to and including the leaf. */
  path: Rule[];
}

/** Every leaf, in every program, that the course can count toward, in tree order. */
export const findMatches = (programs: Program[], course: MatchableCourse): Match[] => {
  const matches: Match[] = [];
  programs.forEach((program) => {
    const visit = (rule: Rule, path: Rule[]) => {
      const here = [...path, rule];
      if (!isLeaf(rule)) {
        rule.rules.forEach((child) => visit(child, here));
      } else if (rule.q_json && courseMatches(rule.q_json, course)) {
        matches.push({ program, leaf: rule, path: here });
      }
    };
    program.rules.forEach((rule) => visit(rule, []));
  });
  return matches;
};

/** Node ids of each match's program, the groups above it and the leaf itself. */
export const matchNodeIds = (matches: Match[]): Set<string> =>
  new Set(
    matches.flatMap(({ program, path }) => [
      program.key,
      ...path.map((rule) => ruleNodeId(program, rule)),
    ])
  );
