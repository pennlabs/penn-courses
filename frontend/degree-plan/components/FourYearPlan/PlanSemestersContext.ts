import { createContext } from "react";

/** The active plan's semester keys, e.g. "2026C", for components outside the plan panel. */
export const PlanSemestersContext = createContext<{
  semesters: string[];
  setSemesters: (semesters: string[]) => void;
}>({ semesters: [], setSemesters: () => {} });
