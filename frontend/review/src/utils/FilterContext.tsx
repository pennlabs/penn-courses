import React, { createContext, useContext, useReducer, ReactNode } from "react";
import {
  DEFAULT_FILTERS,
  FilterState,
  loadStateFromURL,
  normalizeFilters,
} from "./filters";

export type { FilterState } from "./filters";
export { DEFAULT_FILTERS } from "./filters";

export type FilterAction =
  | { type: "SET_DEPARTMENTS"; payload: string[] }
  | { type: "SET_ATTRIBUTES"; payload: string[] }
  | { type: "SET_TIME"; payload: string }
  | { type: "SET_DAYS"; payload: string[] }
  | { type: "SET_SEMESTER"; payload: string }
  | { type: "SET_COURSE_QUALITY"; payload: number[] }
  | { type: "SET_INSTRUCTOR_QUALITY"; payload: number[] }
  | { type: "SET_DIFFICULTY"; payload: number[] }
  | { type: "SET_ALL"; payload: FilterState }
  | { type: "RESET" };

// Every transition is normalized so a semester-specific filter can never coexist with "Any".
export const filterReducer = (
  state: FilterState,
  action: FilterAction
): FilterState => normalizeFilters(applyFilterAction(state, action));

const applyFilterAction = (
  state: FilterState,
  action: FilterAction
): FilterState => {
  switch (action.type) {
    case "SET_DEPARTMENTS":
      return { ...state, departments: action.payload };
    case "SET_ATTRIBUTES":
      return { ...state, attributes: action.payload };
    case "SET_TIME":
      return { ...state, time: action.payload };
    case "SET_DAYS":
      return { ...state, days: action.payload };
    case "SET_SEMESTER":
      // Choosing "Any" would otherwise be snapped straight back by normalizeFilters, so
      // honor the choice by dropping the filters that only make sense for one semester.
      if (action.payload === "Any") {
        return {
          ...state,
          semester: action.payload,
          time: DEFAULT_FILTERS.time,
          days: [...DEFAULT_FILTERS.days],
          instructor_quality: [...DEFAULT_FILTERS.instructor_quality],
        };
      }
      return { ...state, semester: action.payload };
    case "SET_COURSE_QUALITY":
      return { ...state, course_quality: action.payload };
    case "SET_INSTRUCTOR_QUALITY":
      return { ...state, instructor_quality: action.payload };
    case "SET_DIFFICULTY":
      return { ...state, difficulty: action.payload };
    case "SET_ALL":
      return action.payload;
    case "RESET":
      return DEFAULT_FILTERS;
    default:
      return state;
  }
};

const FilterStateContext = createContext<FilterState | undefined>(undefined);
const FilterDispatchContext = createContext<
  React.Dispatch<FilterAction> | undefined
>(undefined);

export const FilterProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {

  const [state, dispatch] = useReducer(
    filterReducer,
    undefined,
    () => loadStateFromURL()
  );

  return (
    <FilterStateContext.Provider value={state}>
      <FilterDispatchContext.Provider value={dispatch}>
        {children}
      </FilterDispatchContext.Provider>
    </FilterStateContext.Provider>
  );
};

export const useFilterState = (): FilterState => {
  const context = useContext(FilterStateContext);
  if (context === undefined) {
    throw new Error("useFilterState must be used within a FilterProvider");
  }
  return context;
};

export const useFilterDispatch = (): React.Dispatch<FilterAction> => {
  const context = useContext(FilterDispatchContext);
  if (context === undefined) {
    throw new Error("useFilterDispatch must be used within a FilterProvider");
  }
  return context;
};
