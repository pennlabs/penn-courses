import styled from "@emotion/styled";
import { color } from "./onboardingStyles";

const Toggle = styled.label<{ $on: boolean }>`
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid
    ${(props) => (props.$on ? "var(--program-major-border)" : color.border)};
  border-radius: 12px;
  background: ${(props) => (props.$on ? "var(--program-major-bg)" : "#fff")};
  cursor: pointer;
  transition: background 150ms ease, border-color 150ms ease;

  &:hover {
    border-color: var(--program-major-border);
  }

  &:focus-within {
    box-shadow: ${color.focusRing};
  }

  input {
    width: 18px;
    height: 18px;
    margin: 0;
    accent-color: var(--program-major);
    cursor: pointer;
  }
`;

const Icon = styled.i`
  width: 1.25rem;
  text-align: center;
  font-size: 18px;
  color: var(--program-major);
`;

const Text = styled.span`
  display: flex;
  flex-direction: column;
  gap: 2px;
`;

const Label = styled.span`
  font-size: 15px;
  font-weight: 600;
  color: ${color.heading};
`;

const Hint = styled.span`
  font-size: 13px;
  color: ${color.muted};
`;

interface PremedFieldProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

/** Whether the plan tracks the courses medical schools ask for, as a program of its own. */
const PremedField = ({ checked, onChange, disabled }: PremedFieldProps) => (
  <Toggle $on={checked}>
    <input
      type="checkbox"
      checked={checked}
      disabled={disabled}
      onChange={(e) => onChange(e.target.checked)}
    />
    <Icon className="fas fa-stethoscope" aria-hidden />
    <Text>
      <Label>I&apos;m interested in studying pre-medicine</Label>
      <Hint>
        Adds the courses most medical schools ask for. They count toward your
        other programs too.
      </Hint>
    </Text>
  </Toggle>
);

export default PremedField;
