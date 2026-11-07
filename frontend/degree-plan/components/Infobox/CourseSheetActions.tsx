import React, { useContext, useMemo, useState } from "react";
import styled from "@emotion/styled";
import useSWR, { useSWRConfig } from "swr";
import { DegreePlan, DockedCourse, Fulfillment } from "@/types";
import { postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { rulesByProgram, RuleInProgram } from "@/utils/programs";
import ToastContext from "@/components/Toast/Toast";

const Section = styled.div`
  margin-top: 0.85rem;
`;

const Label = styled.div`
  margin-bottom: 0.35rem;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--primary-color-xxx-dark);
`;

const RuleRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.45rem 0;
  font-size: 0.9rem;
  color: var(--primary-color-ultra-dark);

  & + & {
    border-top: 1px solid rgba(129, 154, 225, 0.25);
  }
`;

const Program = styled.span`
  margin-right: 0.3rem;
  font-weight: 600;
  color: var(--primary-color-xxx-dark);
`;

const SmallButton = styled.button`
  flex-shrink: 0;
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--primary-color-xx-dark);
  border-radius: 6px;
  background: #ffffff;
  color: var(--primary-color-xx-dark);
  font-family: inherit;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;

  &:disabled {
    opacity: 0.55;
    cursor: default;
  }
`;

const Buttons = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.85rem;
`;

const ActionButton = styled.button<{ $danger?: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.6rem 0.85rem;
  border: 1px solid
    ${(props) =>
      props.$danger
        ? "var(--error-color, #e66161)"
        : "rgba(129, 154, 225, 0.6)"};
  border-radius: 0.3rem;
  background: #ffffff;
  color: ${(props) =>
    props.$danger
      ? "var(--error-color, #e66161)"
      : "var(--primary-color-ultra-dark)"};
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
`;

interface CourseSheetActionsProps {
  fullCode: string;
  degreePlanId: DegreePlan["id"];
  onDone: () => void;
}

// What a phone can't do by dragging: dock, remove, and choose the requirement a course counts for.
const CourseSheetActions = ({
  fullCode,
  degreePlanId,
  onDone,
}: CourseSheetActionsProps) => {
  const showToast = useContext(ToastContext);
  const { mutate } = useSWRConfig();
  const fulfillmentsKey = `/api/degree/degreeplans/${degreePlanId}/fulfillments`;
  const { data: fulfillments } = useSWR<Fulfillment[]>(fulfillmentsKey);
  const { data: plan } = useSWR<DegreePlan>(
    `/api/degree/degreeplans/${degreePlanId}`
  );
  const { data: docked = [] } = useSWR<DockedCourse[]>("/api/degree/docked");
  const { remove: removeFulfillment } = useSWRCrud<Fulfillment>(
    fulfillmentsKey,
    {
      idKey: "full_code",
    }
  );
  const { createOrUpdate: dock, remove: undock } = useSWRCrud<DockedCourse>(
    "/api/degree/docked",
    { idKey: "full_code" }
  );
  const [switching, setSwitching] = useState<number | null>(null);

  const fulfillment = fulfillments?.find((f) => f.full_code === fullCode);
  const isDocked = docked.some((course) => course.full_code === fullCode);
  const code = fullCode.replace("-", " ");

  const rules = useMemo(
    () => (plan ? rulesByProgram(plan) : new Map<number, RuleInProgram>()),
    [plan]
  );
  const named = (ids: number[] = []) =>
    ids.flatMap((id) => {
      const rule = rules.get(id);
      return rule ? [{ ...rule, id }] : [];
    });
  const countsFor = named(fulfillment?.rules);
  const couldCountFor = named(fulfillment?.unselected_rules);

  const removeFromPlan = async () => {
    removeFulfillment(fullCode);
    dock({ full_code: fullCode }, fullCode);
    await mutate(fulfillmentsKey);
    showToast(`Moved ${code} to Docked`, false);
    onDone();
  };

  const switchTo = async (ruleId: number) => {
    setSwitching(ruleId);
    try {
      const res = await postFetcher(
        `/api/degree/degreeplans/${degreePlanId}/fulfillments/${fullCode}/switch-rule`,
        { rule_id: ruleId }
      );
      await Promise.all([
        mutate(fulfillmentsKey),
        mutate(`/api/degree/degreeplans/${degreePlanId}`),
      ]);
      const displaced: { full_code: string; removed: boolean }[] =
        res?.displaced ?? [];
      showToast(
        displaced.length
          ? displaced
              .map(({ full_code, removed }) =>
                removed
                  ? `${full_code.replace(
                      "-",
                      " "
                    )} was removed (it no longer fulfills any rules).`
                  : `${full_code.replace(
                      "-",
                      " "
                    )} was displaced from this rule.`
              )
              .join(" ")
          : `${code} now counts for ${rules.get(ruleId)?.title ?? "that rule"}`,
        false
      );
    } catch {
      showToast(`Couldn't switch ${code}. Try again.`, true);
    } finally {
      setSwitching(null);
    }
  };

  return (
    <>
      {countsFor.length > 0 && (
        <Section>
          <Label>Counts for</Label>
          {countsFor.map((rule) => (
            <RuleRow key={rule.id}>
              <span>
                <Program>{rule.program.code}</Program>
                {rule.title}
              </span>
            </RuleRow>
          ))}
        </Section>
      )}
      {couldCountFor.length > 0 && (
        <Section>
          <Label>Could count for instead</Label>
          {couldCountFor.map((rule) => (
            <RuleRow key={rule.id}>
              <span>
                <Program>{rule.program.code}</Program>
                {rule.title}
              </span>
              <SmallButton
                type="button"
                disabled={switching !== null}
                onClick={() => switchTo(rule.id)}
              >
                {switching === rule.id ? "Switching…" : "Count here"}
              </SmallButton>
            </RuleRow>
          ))}
        </Section>
      )}
      <Buttons>
        {fulfillment ? (
          <ActionButton type="button" $danger onClick={removeFromPlan}>
            <i className="fas fa-times" aria-hidden />
            Remove from plan
          </ActionButton>
        ) : isDocked ? (
          <ActionButton
            type="button"
            onClick={() => {
              undock(fullCode);
              onDone();
            }}
          >
            <i className="fas fa-archive" aria-hidden />
            Remove from Docked
          </ActionButton>
        ) : (
          <ActionButton
            type="button"
            onClick={() => {
              dock({ full_code: fullCode }, fullCode);
              showToast(`Saved ${code} to Docked`, false);
              onDone();
            }}
          >
            <i className="fas fa-archive" aria-hidden />
            Save for later
          </ActionButton>
        )}
      </Buttons>
    </>
  );
};

export default CourseSheetActions;
