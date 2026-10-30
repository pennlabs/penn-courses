/**
 * Renders a rule's q_json (see Rule.get_json_q_object on the backend) as text a person can
 * read, e.g. `CIS 1200 or (dept MATH and level ≥ 2000)`.
 */

type QJson =
  | { type: "AND" | "OR" | "NOT"; clauses: QJson[] }
  | { type: "COURSE"; full_code: string }
  | { type: "LEAF"; key: string; value: unknown };

const formatCode = (fullCode: string) => fullCode.replace("-", " ");

const formatValue = (value: unknown): string =>
  Array.isArray(value) ? value.join(", ") : String(value);

const LEAF_LABELS: Record<string, (value: unknown) => string> = {
  full_code: (v) => formatCode(String(v)),
  full_code__startswith: (v) => `${formatCode(String(v))}*`,
  semester: (v) => `taken ${v}`,
  department__code: (v) => `dept ${v}`,
  department__code__in: (v) => `dept in {${formatValue(v)}}`,
  attributes__code__in: (v) => `attribute in {${formatValue(v)}}`,
  code: (v) => `number ${v}`,
  code__gte: (v) => `number ≥ ${v}`,
  code__lte: (v) => `number ≤ ${v}`,
  code__gt: (v) => `number > ${v}`,
  code__lt: (v) => `number < ${v}`,
};

const leafToText = (key: string, value: unknown) =>
  LEAF_LABELS[key]?.(value) ?? `${key} = ${formatValue(value)}`;

export const qToText = (q: QJson | null | undefined, nested = false): string => {
  if (!q) return "";
  switch (q.type) {
    case "COURSE":
      return formatCode(q.full_code);
    case "LEAF":
      return leafToText(q.key, q.value);
    case "NOT":
      return `not ${qToText(q.clauses[0], true)}`;
    case "AND":
    case "OR": {
      if (q.clauses.length === 1) return qToText(q.clauses[0], nested);
      const text = q.clauses
        .map((clause) => qToText(clause, true))
        .join(q.type === "AND" ? " and " : " or ");
      return nested ? `(${text})` : text;
    }
    default:
      return JSON.stringify(q);
  }
};

