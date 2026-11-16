// A catalog row a school card can resolve to: a degree, or a major added on top of one.
export interface CatalogRow {
  id: number;
  major: string;
  major_name: string;
  concentration: string | null;
  concentration_name: string | null;
  year: number;
  // Set when the same major code exists in more than one school, so those rows stay apart.
  choiceKey?: string;
}

export const rowKey = (row: CatalogRow) => row.choiceKey || row.major;

const NONE = new Set(["", "none"]);

export const concentrationKey = (row: CatalogRow) => {
  const code = (row.concentration || "").trim();
  return NONE.has(code.toLowerCase()) ? "" : code;
};

const byName = (a: CatalogRow, b: CatalogRow) =>
  (a.major_name || a.major).localeCompare(b.major_name || b.major);

// One row per major name. Catalog years and concentrations are later steps.
export const majorChoices = (rows: CatalogRow[]): CatalogRow[] => {
  const byMajor = new Map<string, CatalogRow>();
  rows.forEach((row) => {
    const key = rowKey(row);
    if (!byMajor.has(key)) byMajor.set(key, row);
  });
  return [...byMajor.values()].sort(byName);
};

export const concentrationChoices = (rows: CatalogRow[], major: string): CatalogRow[] => {
  const seen = new Map<string, CatalogRow>();
  rows
    .filter((row) => rowKey(row) === major)
    .forEach((row) => {
      const key = concentrationKey(row);
      if (!seen.has(key)) seen.set(key, row);
    });
  return [...seen.values()].sort((a, b) =>
    (a.concentration_name || "").localeCompare(b.concentration_name || "")
  );
};

export const yearChoices = (
  rows: CatalogRow[],
  major: string,
  concentration: string
): CatalogRow[] =>
  rows
    .filter((row) => rowKey(row) === major && concentrationKey(row) === concentration)
    .sort((a, b) => b.year - a.year);

// The catalog year at or before the student's start year, or the earliest later one.
export const defaultYear = (years: number[], startYear: number | null): number | null => {
  if (!years.length) return null;
  if (startYear == null) return Math.max(...years);
  const atOrBefore = years.filter((year) => year <= startYear);
  return atOrBefore.length ? Math.max(...atOrBefore) : Math.min(...years);
};

export const concentrationLabel = (row: CatalogRow) =>
  concentrationKey(row) ? row.concentration_name || row.concentration || "" : "No concentration";
