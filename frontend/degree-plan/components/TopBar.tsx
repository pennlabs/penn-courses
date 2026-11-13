import React from "react";
import styled from "@emotion/styled";
import { useRouter } from "next/router";
// TODO: Move shared components to typescript
// @ts-ignore
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import { User } from "@/types";
import NotificationBell from "./NotificationBell";
import { tourTarget } from "./Tour/OnboardingTour";

const Bar = styled.header`
  /* Above the body's isolated stacking context, so the account menu covers it, but below modals. */
  position: relative;
  z-index: 2;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.65rem 1.5rem;
  background: #ffffff;
  border-bottom: 1px solid rgba(129, 154, 225, 0.35);

  @media (max-width: 767px) {
    padding: 0.5rem 1rem;
  }
`;

const Brand = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
`;

const Logo = styled.img`
  display: block;
  flex-shrink: 0;
`;

const Title = styled.span`
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--primary-color-ultra-dark);
`;

const Actions = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
`;

const ColumnToggles = styled.div`
  display: flex;
  align-items: center;
  gap: 0.35rem;
`;

const ColumnToggle = styled.button<{ $isOpen: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.55rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-family: inherit;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  color: ${(props) =>
    props.$isOpen
      ? "var(--primary-color-xx-dark)"
      : "var(--primary-color-ultra-dark)"};
  transition: color 120ms ease;

  &:hover {
    color: ${(props) =>
      props.$isOpen ? "var(--primary-color-xxx-dark)" : "#2a2e5c"};
  }
`;

const TourButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 1.1rem;
  color: var(--primary-color-ultra-dark);
  cursor: pointer;

  &:hover {
    background: var(--primary-color-light);
  }
`;

interface TopBarProps {
  user: User | null;
  login: (u: User) => void;
  logout: () => void;
  planOpen: boolean;
  setPlanOpen: (open: boolean) => void;
  requirementsOpen: boolean;
  setRequirementsOpen: (open: boolean) => void;
  showColumnToggles: boolean; // the columns don't exist during onboarding
  onStartTour?: () => void; // the tour has nothing to show during onboarding
}

const TopBar = ({
  user,
  login,
  logout,
  planOpen,
  setPlanOpen,
  requirementsOpen,
  setRequirementsOpen,
  showColumnToggles,
  onStartTour,
}: TopBarProps) => {
  const { asPath } = useRouter();

  return (
    <Bar>
      <Brand>
        <Logo src="pdp-logo.svg" alt="" width="30" height="45" />
        <Title>Penn Degree Plan</Title>
      </Brand>
      <Actions>
        {showColumnToggles && (
          <ColumnToggles role="group" aria-label="Toggle columns" {...tourTarget("column-toggles")}>
            <ColumnToggle
              type="button"
              $isOpen={planOpen}
              aria-pressed={planOpen}
              onClick={() => setPlanOpen(!planOpen)}
            >
              <i className="fas fa-calendar-alt" aria-hidden />
              <span>Plan</span>
            </ColumnToggle>
            <ColumnToggle
              type="button"
              $isOpen={requirementsOpen}
              aria-pressed={requirementsOpen}
              onClick={() => setRequirementsOpen(!requirementsOpen)}
            >
              {/* fa-list-check in the prototype; Font Awesome 5 calls it fa-tasks. */}
              <i className="fas fa-tasks" aria-hidden />
              <span>Requirements</span>
            </ColumnToggle>
          </ColumnToggles>
        )}
        {onStartTour && (
          <TourButton
            type="button"
            aria-label="Take the tour"
            title="Take the tour"
            onClick={onStartTour}
            {...tourTarget("replay-tour")}
          >
            <i className="far fa-question-circle" aria-hidden />
          </TourButton>
        )}
        {user && <NotificationBell />}
        <AccountIndicator
          user={user}
          backgroundColor="light"
          nameLength={2}
          login={login}
          logout={logout}
          pathname={asPath}
        />
      </Actions>
    </Bar>
  );
};

export default TopBar;
