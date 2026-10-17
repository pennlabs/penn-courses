import styled from "@emotion/styled";
import useSWR, { useSWRConfig } from "swr";
import { deleteFetcher } from "@/hooks/swrcrud";
import { PlanSummary } from "@/types";

const Bar = styled.div`
  margin: 0 0 2px;
  padding: 6px 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  font-size: var(--type-body);
  background: #fff;
`;

const Row = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
`;

const VIOLATION_LABELS: { [kind: string]: string } = {
  too_many_degrees: "claimed by more than two degrees",
  undergrad_grad_cu: "exceeds the 3 CU bachelor's/master's share",
  grad_grad: "shared by two graduate programs",
  also_offered: "is the same course as another listing",
  mutually_exclusive: "conflicts with a mutually exclusive course on the plan",
};

export const violationMessage = (kind: string) =>
  VIOLATION_LABELS[kind] ?? "illegally double counted";

const PlanSummaryBar = ({ degreePlanId }: { degreePlanId: number }) => {
  const { mutate } = useSWRConfig();
  const { data } = useSWR<PlanSummary>(`/api/degree/degreeplans/${degreePlanId}/summary`);
  if (!data) return null;
  const hasNamedProgram = Boolean(data.dual_program);
  const hasCas = Boolean(data.cas);
  const hasViolations = data.violations.length > 0;
  if (!hasNamedProgram && !hasCas && !hasViolations) return null;

  const clearDual = async () => {
    await deleteFetcher(`/api/degree/degreeplans/${degreePlanId}/dual-program`);
    await mutate(`/api/degree/degreeplans/${degreePlanId}`);
    await mutate(`/api/degree/degreeplans/${degreePlanId}/fulfillments`);
    await mutate(`/api/degree/degreeplans/${degreePlanId}/summary`);
  };

  return (
    <Bar>
      {hasNamedProgram && (
        <Row>
          <strong>{data.dual_program?.name}</strong>
          <button type="button" onClick={clearDual}>
            Clear dual program
          </button>
        </Row>
      )}
      {data.cas && (
        <div>
          {Number(data.cas.floor)} CU degree, {Number(data.cas.shared_cu)} CU shared across majors,{" "}
          {Number(data.cas.remaining)} CU remaining
        </div>
      )}
      {data.violations.length > 0 && (
        <ul>
          {data.violations.map((violation) => (
            <li key={`${violation.full_code}-${violation.kind}`}>
              {violation.message
                || `${violation.full_code.replace("-", " ")} ${violationMessage(violation.kind)}`}
            </li>
          ))}
        </ul>
      )}
    </Bar>
  );
};

export default PlanSummaryBar;
