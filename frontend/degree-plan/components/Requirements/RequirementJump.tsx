import styled from "@emotion/styled";
import { navigateToRule } from "@/hooks/requirementNav";

const InfoButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 1rem;
  height: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  font-size: var(--type-body);
  line-height: 1;
  flex-shrink: 0;

  &:hover {
    color: #555;
  }
`;

interface RequirementJumpProps {
  ruleIds: number[];
  cycleKey: string;
}

/** Info button on a suggested course. Clicking it opens that requirement. */
const RequirementJump = ({ ruleIds, cycleKey }: RequirementJumpProps) => {
  const ids = ruleIds.filter((id) => id != null);
  if (!ids.length) return null;
  const title = ids.length > 1
    ? "Show in requirements. Click again for the next one."
    : "Show in requirements";
  return (
    <InfoButton
      type="button"
      title={title}
      aria-label={title}
      onMouseDown={(event) => event.stopPropagation()}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        navigateToRule(cycleKey, ids);
      }}
    >
      <i className="fas fa-info-circle" />
    </InfoButton>
  );
};

export default RequirementJump;
