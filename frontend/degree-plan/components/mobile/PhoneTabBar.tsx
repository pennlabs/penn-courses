import styled from "@emotion/styled";
import { useRef } from "react";
import useBottomOffset from "@/hooks/useBottomOffset";
import { tourTarget } from "@/components/Tour/OnboardingTour";

export type PhoneTab = "plan" | "requirements" | "search" | "docked";

const TABS: { id: PhoneTab; label: string; icon: string }[] = [
  { id: "plan", label: "Plan", icon: "fa-calendar-alt" },
  { id: "requirements", label: "Requirements", icon: "fa-tasks" },
  { id: "search", label: "Add Course", icon: "fa-plus-circle" },
  { id: "docked", label: "Docked", icon: "fa-archive" },
];

export const PHONE_TABS = TABS.map(({ id }) => id);

const Bar = styled.nav`
  flex-shrink: 0;
  display: flex;
  margin: 0 0.5rem calc(0.5rem + env(safe-area-inset-bottom));
  padding: 0.15rem 0.25rem;
  background: #ffffff;
  border: 1px solid rgba(129, 154, 225, 0.35);
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(30, 32, 60, 0.14);
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

const PhoneTabBar = ({ active, onSelect, dockedCount }: PhoneTabBarProps) => {
  const ref = useRef<HTMLElement>(null);
  useBottomOffset(ref);
  return (
    <Bar aria-label="Sections" ref={ref}>
      {TABS.map(({ id, label, icon }) => (
        <Tab
          key={id}
          type="button"
          {...tourTarget(`phone-tab-${id}`)}
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
};

export default PhoneTabBar;
