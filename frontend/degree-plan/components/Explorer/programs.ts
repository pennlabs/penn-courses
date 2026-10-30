import type { Degree, DegreeListing, Major, Minor, Rule } from "@/types";

/**
 * A Degree is a student's whole program (e.g. a SEAS BSE); a Major or Minor is only the block
 * it adds on top of one. A dual degree across two schools is two Degrees.
 */
export type ProgramKind = "degree" | "major" | "minor";

export interface ProgramRef {
  kind: ProgramKind;
  id: number;
}

/** A degree, major or minor, in the one shape the explorer draws. */
export interface Program extends ProgramRef {
  /** Unique across kinds, e.g. "major-12". Also how the program is written in the URL. */
  key: string;
  name: string;
  /** A short second line, e.g. "Degree · EU_BSE · 2025". */
  summary: string;
  /** Label and value pairs for the detail panel. */
  facts: [string, string | number][];
  rules: Rule[];
}

export type MajorListing = Omit<Major, "rules">;
export type MinorListing = Omit<Minor, "rules">;

export const ENDPOINTS: Record<ProgramKind, string> = {
  degree: "/api/degree/degrees",
  major: "/api/degree/majors",
  minor: "/api/degree/minors",
};

export const KIND_LABELS: Record<ProgramKind, string> = {
  degree: "Degree",
  major: "Major",
  minor: "Minor",
};

const KINDS = Object.keys(ENDPOINTS) as ProgramKind[];

export const programKey = ({ kind, id }: ProgramRef) => `${kind}-${id}`;

/** Reads a URL value like "degree-3,major-12". Malformed or repeated entries are dropped. */
export const parseProgramKeys = (value: string | string[] | undefined): ProgramRef[] => {
  if (typeof value !== "string") return [];
  const refs = new Map<string, ProgramRef>();
  value.split(",").forEach((part) => {
    const [kind, id] = part.split("-");
    if (KINDS.includes(kind as ProgramKind) && /^\d+$/.test(id ?? "")) {
      const ref = { kind: kind as ProgramKind, id: Number(id) };
      refs.set(programKey(ref), ref);
    }
  });
  return Array.from(refs.values());
};

const join = (parts: (string | number | false | null | undefined)[]) =>
  parts.filter(Boolean).join(" · ");

export const degreeLabel = (d: DegreeListing | Degree) =>
  join([d.year, d.degree, d.major_name || d.major, d.concentration_name || d.concentration]);

export const componentLabel = (c: MajorListing | MinorListing) =>
  join([
    c.year,
    c.name || c.code,
    "concentration" in c && (c.concentration_name || c.concentration),
    c.program_code,
  ]);

export const toProgram = (ref: ProgramRef, data: Degree | Major | Minor): Program => {
  const key = programKey(ref);
  if (ref.kind === "degree") {
    const d = data as Degree;
    const concentration = d.concentration_name || d.concentration;
    return {
      ...ref,
      key,
      name: join([d.degree, d.major_name || d.major]),
      summary: join([KIND_LABELS.degree, d.program, d.year, concentration]),
      facts: [
        ["Degree id", d.id],
        ["Program", d.program],
        ["Major", d.major],
        ["Concentration", concentration || "—"],
        ["Year", d.year],
        ["Top-level rules", d.rules.length],
      ],
      rules: d.rules,
    };
  }
  const c = data as Major | Minor;
  const concentration = "concentration" in c ? c.concentration_name || c.concentration : null;
  return {
    ...ref,
    key,
    name: c.name || c.code,
    summary: join([KIND_LABELS[ref.kind], c.program_code, c.year, concentration]),
    facts: [
      [`${KIND_LABELS[ref.kind]} id`, c.id],
      ["Program code", c.program_code],
      ["Code", c.code],
      ...(concentration ? [["Concentration", concentration] as [string, string]] : []),
      ["Year", c.year],
      ["Top-level rules", c.rules.length],
    ],
    rules: c.rules,
  };
};
