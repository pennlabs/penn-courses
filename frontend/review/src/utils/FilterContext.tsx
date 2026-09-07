import React, { createContext, useContext, useReducer, ReactNode } from "react";
import {
  DEFAULT_FILTERS,
  FilterState,
  loadStateFromURL,
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

export const filterReducer = (
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

// State and dispatch are deliberately separate contexts: components that only
// write filters (the header's reset, the department shortcut links) subscribe
// to dispatch alone, whose identity is stable for the life of the provider, so
// they don't re-render on every keystroke or slider drag.
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
