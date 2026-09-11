export interface FilterState {
  departments: string[];
  attributes: string[];
  time: string;
  days: string[];
  semester: string;
  course_quality: number[];
  instructor_quality: number[];
  difficulty: number[];
}

export type FilterKey = keyof FilterState;

export const DEFAULT_FILTERS: FilterState = {
  departments: [],
  attributes: [],
  time: "6.00-22.00",
  days: ["M", "T", "W", "R", "F"],
  semester: "Next Available",
  course_quality: [0, 4],
  instructor_quality: [0, 4],
  difficulty: [0, 4],
};

// Freeze so changing by accident forces an error
Object.freeze(DEFAULT_FILTERS);
Object.values(DEFAULT_FILTERS).forEach((v) => Object.freeze(v));

export const FILTER_KEYS = Object.keys(DEFAULT_FILTERS) as FilterKey[];

// Ratings are stored as [min, max] pairs and serialized as "min-max"
const RANGE_KEYS: FilterKey[] = [
  "course_quality",
  "instructor_quality",
  "difficulty",
];

export const SEMESTER_OPTIONS = ["Any", "Next Available"];

const TIME_PATTERN = /^([01]?\d|2[0-3])\.[0-5]\d-([01]?\d|2[0-3])\.[0-5]\d$/;

export const isValidTimeString = (value: string): boolean =>
  TIME_PATTERN.test(value);

export const isFilterDefault = <K extends FilterKey>(
  key: K,
  value: FilterState[K]
): boolean => {
  const def = DEFAULT_FILTERS[key];
  if (Array.isArray(value) && Array.isArray(def)) {
    const defValues = def as (string | number)[];
    return (
      value.length === defValues.length &&
      value.every((v: string | number) => defValues.includes(v))
    );
  }
  return value === def;
};

export const changedFilterKeys = (filters: FilterState): FilterKey[] =>
  FILTER_KEYS.filter((key) => !isFilterDefault(key, filters[key]));

/**
 `semester` change alone counts as zero since semester is always sent to the API, so on its own it does not
 count as "filtering" and should not trigger a search.
 */
export const countActiveFilters = (filters: FilterState): number => {
  const changed = changedFilterKeys(filters);
  return changed.some((key) => key !== "semester") ? changed.length : 0;
};

// Filters the backend only accepts for the current semester
export const SEMESTER_SPECIFIC_FILTERS: FilterKey[] = [
  "instructor_quality",
  "days",
  "time",
];

export const SEMESTER_FILTER_LABELS: Partial<Record<FilterKey, string>> = {
  instructor_quality: "Instructor Quality",
  days: "Days Offered",
  time: "Time Offered",
};

export const getActiveSemesterFilters = (filters: FilterState): FilterKey[] =>
  SEMESTER_SPECIFIC_FILTERS.filter(
    (key) => !isFilterDefault(key, filters[key])
  );

export const formatFiltersForAPI = (
  filters: FilterState
): Record<string, string> => {
  const formatted: Record<string, string> = {};

  FILTER_KEYS.forEach((key) => {
    const value = filters[key];

    // Always sent, default or not — the endpoint is semester-scoped.
    if (key === "semester") {
      formatted[key] = value === "Any" ? "all" : "current";
      return;
    }
    if (isFilterDefault(key, value)) return;

    if (RANGE_KEYS.includes(key)) {
      const [min, max] = value as number[];
      formatted[key] = `${min}-${max}`;
    } else if (key === "days") {
      formatted[key] = (value as string[]).join("");
    } else if (key === "time") {
      formatted[key] = value as string;
    } else if (key === "attributes" || key === "departments") {
      formatted[key] = (value as string[]).join("|");
    }
  });

  return formatted;
};

export const getFilteredURL = (filters: FilterState): string => {
  const params = new URLSearchParams();

  FILTER_KEYS.forEach((key) => {
    if (isFilterDefault(key, filters[key])) return;
    const value = filters[key];
    params.append(key, Array.isArray(value) ? value.join(",") : value);
  });

  const query = params.toString();
  return query ? `/?${query}` : "/";
};

export const loadStateFromURL = (
  search: string = window.location.search
): FilterState => {
  const params = new URLSearchParams(search);
  const filters: FilterState = {
    ...DEFAULT_FILTERS,
    // Copy arrays so we don't mutate the frozen defaults
    departments: [...DEFAULT_FILTERS.departments],
    attributes: [...DEFAULT_FILTERS.attributes],
    days: [...DEFAULT_FILTERS.days],
    course_quality: [...DEFAULT_FILTERS.course_quality],
    instructor_quality: [...DEFAULT_FILTERS.instructor_quality],
    difficulty: [...DEFAULT_FILTERS.difficulty],
  };

  FILTER_KEYS.forEach((key) => {
    const raw = params.get(key);
    if (raw === null) return;

    if (RANGE_KEYS.includes(key)) {
      const nums = raw.split(",").map(Number);
      if (nums.length === 2 && nums.every((n) => Number.isFinite(n))) {
        (filters[key] as number[]) = nums;
      }
    } else if (key === "time") {
      if (isValidTimeString(raw)) filters.time = raw;
    } else if (key === "semester") {
      if (SEMESTER_OPTIONS.includes(raw)) filters.semester = raw;
    } else {
      (filters[key] as string[]) = raw.split(",").filter(Boolean);
    }
  });

  return filters;
};
