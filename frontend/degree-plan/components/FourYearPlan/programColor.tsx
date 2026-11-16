import { useMemo } from "react";
import styled from "@emotion/styled";
import useSWR from "swr";
import { DegreePlan, PlanSummary, Rule } from "@/types";

/** Same palette as the planner: one color per program, in plan order. */
export const PROGRAM_COLORS = ["#a51c30", "#2563eb", "#d97706", "#7c3aed"];

export const programColor = (index: number) =>
  PROGRAM_COLORS[index % PROGRAM_COLORS.length];

const Bar = styled.div`
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  display: flex;
  flex-direction: column;
  border-radius: 3px 0 0 3px;
  overflow: hidden;
  pointer-events: none;
`;

const Stripe = styled.div`
  flex: 1;
  min-height: 0;
`;

const walkRules = (rules: Rule[] | undefined, key: string, into: Map<number, string>) => {
  for (const rule of rules ?? []) {
    into.set(rule.id, key);
    if (rule.rules?.length) walkRules(rule.rules, key, into);
  }
};

/** Program keys a placed course claims, and the keys a suggestion's rules belong to. */
export const useProgramClaims = (planId?: number | null) => {
  const { data: detail } = useSWR<DegreePlan>(
    planId ? `/api/degree/degreeplans/${planId}` : null
  );
  const { data: summary } = useSWR<PlanSummary>(
    planId ? `/api/degree/degreeplans/${planId}/summary` : null
  );

  return useMemo(() => {
    const components = detail?.components ?? [];
    const order = components.map((component) => component.key);
    const titles: Record<string, string> = {};
    const ruleToKey = new Map<number, string>();
    for (const component of components) {
      titles[component.key] = component.title;
      walkRules(component.rules, component.key, ruleToKey);
    }
    const sortKeys = (keys: string[]) => {
      const known = order.filter((key) => keys.includes(key));
      const rest = keys.filter((key) => !order.includes(key));
      return [...known, ...rest];
    };
    return {
      order,
      titles,
      claimsFor(fullCode: string) {
        return sortKeys(summary?.course_claims?.[fullCode] ?? []);
      },
      claimsForRules(ruleIds: number[]) {
        const keys = new Set<string>();
        for (const id of ruleIds) {
          const key = ruleToKey.get(id);
          if (key) keys.add(key);
        }
        return sortKeys([...keys]);
      },
    };
  }, [detail, summary]);
};

export const ClaimBar = ({
  keys,
  order,
  titles,
}: {
  keys: string[];
  order: string[];
  titles: Record<string, string>;
}) => {
  if (keys.length === 0) return null;
  const label = keys.map((key) => titles[key] || key).join(", ");
  return (
    <Bar title={label} aria-hidden="true">
      {keys.map((key) => {
        const index = order.indexOf(key);
        return (
          <Stripe
            key={key}
            style={{ background: programColor(index < 0 ? 0 : index) }}
          />
        );
      })}
    </Bar>
  );
};
