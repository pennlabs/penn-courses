export const breakpoints = {
  xs: 300,
  sm: 700,
  md: 800,
  lg: 900,
  xl: 1200,
  xxl: 1400,
} as const;

export type Breakpoint = keyof typeof breakpoints;

// Applies at or above bp
export const minWidth = (bp: Breakpoint) =>
  `@media screen and (min-width: ${breakpoints[bp]}px)`;

//subtracts 0.02px to avoid overlap with minWidth
export const maxWidth = (bp: Breakpoint) =>
  `@media screen and (max-width: ${breakpoints[bp] - 0.02}px)`;

// Applies between low (inclusive) and high (exclusive).
export const between = (low: Breakpoint, high: Breakpoint) =>
  `@media screen and (min-width: ${breakpoints[low]}px) and (max-width: ${
    breakpoints[high] - 0.02
  }px)`;

// js equivalent of maxWidth, for use in React components
export const isBelow = (bp: Breakpoint) =>
  typeof window !== "undefined" && window.innerWidth < breakpoints[bp];
