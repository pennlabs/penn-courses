import styled from "@emotion/styled";

export type PhoneTab = "plan" | "requirements" | "search" | "docked";

const TABS: { id: PhoneTab; label: string; icon: string }[] = [
  { id: "plan", label: "Plan", icon: "fa-calendar-alt" },
  { id: "requirements", label: "Requirements", icon: "fa-tasks" },
  { id: "search", label: "Add Course", icon: "fa-plus-circle" },
  { id: "docked", label: "Docked", icon: "fa-archive" },
];

const Bar = styled.nav`
  flex-shrink: 0;
  display: flex;
  background: #ffffff;
  border-top: 1px solid rgba(129, 154, 225, 0.35);
  padding-bottom: env(safe-area-inset-bottom);
`;

const Tab = styled.button<{ $active: boolean }>`
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.55rem 0.25rem 0.5rem;
  border: none;
  background: none;
  font-family: inherit;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  color: ${(props) =>
    props.$active
      ? "var(--primary-color-xx-dark)"
      : "var(--primary-color-ultra-dark)"};
  opacity: ${(props) => (props.$active ? 1 : 0.7)};

  i {
    font-size: 1.15rem;
  }
`;

const Count = styled.span`
  position: absolute;
  top: 0.3rem;
  left: calc(50% + 0.5rem);
  min-width: 1.1rem;
  padding: 0 0.3rem;
  border-radius: 999px;
  background: var(--primary-color-xx-dark);
  color: #ffffff;
  font-size: 0.65rem;
  line-height: 1.1rem;
`;

interface PhoneTabBarProps {
  active: PhoneTab;
  onSelect: (tab: PhoneTab) => void;
  dockedCount: number;
}

const PhoneTabBar = ({ active, onSelect, dockedCount }: PhoneTabBarProps) => (
  <Bar aria-label="Sections">
    {TABS.map(({ id, label, icon }) => (
      <Tab
        key={id}
        type="button"
        $active={active === id}
        aria-current={active === id ? "page" : undefined}
        onClick={() => onSelect(id)}
      >
        <i className={`fas ${icon}`} aria-hidden />
        {label}
        {id === "docked" && dockedCount > 0 && <Count>{dockedCount}</Count>}
      </Tab>
    ))}
  </Bar>
);

export default PhoneTabBar;
