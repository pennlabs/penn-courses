/** A card or chip stays readable up to this many characters. Past it, the code is a search. */
export const SHORT_LABEL_MAX = 24;

const shown = (value: string | null | undefined) =>
  (value || "").replace(/-/g, " ").trim();

export function fitsOnCard(text: string | null | undefined): boolean {
  const label = shown(text);
  return label.length > 0 && label.length <= SHORT_LABEL_MAX;
}

/** Schedule card text. A short code stays. A long attribute string becomes the rule title. */
export function scheduleCardTitle(placement: {
  short_label?: string | null;
  label?: string | null;
  full_code?: string | null;
}): string {
  const short = shown(placement.short_label);
  if (fitsOnCard(short)) return short;
  const title = (placement.label || "").trim();
  if (title) return title;
  return short || shown(placement.full_code);
}
