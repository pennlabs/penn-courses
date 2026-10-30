import type { Rule } from "@/types";
import { isLeaf } from "./graph";
import { qToText } from "./qToText";

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** What it takes to satisfy a rule, e.g. "2 of 3" for a group or "1 course · 1 CU" for a leaf. */
export const requirementText = (rule: Rule): string => {
  if (!isLeaf(rule)) {
    return rule.num === null
      ? `All of ${rule.rules.length}`
      : `${rule.num} of ${rule.rules.length}`;
  }
  const parts = [];
  if (rule.num !== null) parts.push(plural(rule.num, "course"));
  if (rule.credits !== null) parts.push(`${Number(rule.credits)} CU`);
  return parts.join(" · ");
};

export const ruleTitle = (rule: Rule): string =>
  rule.title || (isLeaf(rule) ? qToText(rule.q_json) : "") || `Rule ${rule.id}`;

export const blockText = (rule: Rule): string =>
  [rule.block_type, rule.block_value].filter(Boolean).join(" · ");

export const shareTargetText = (rule: Rule): string =>
  rule.share_targets.map(({ kind, value }) => (value ? `${kind} ${value}` : kind)).join(", ");
