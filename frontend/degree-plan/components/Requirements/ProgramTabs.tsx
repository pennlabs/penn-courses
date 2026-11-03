import React, { forwardRef, useEffect, useRef } from "react";
import styled from "@emotion/styled";

export type ProgramKind = "degree" | "major" | "minor";

export interface ProgramTab {
  key: string;
  kind: ProgramKind;
  title: string;
  code: string;
  year: number;
  progress: number; // a number between 0 and 1
}

// Full names fit side by side up to this many programs; beyond that tabs show codes and scroll.
const MAX_TABS_WITH_FULL_NAMES = 2;

const RING_SIZE = 28;
const RING_STROKE = 2.5;
const RING_RADIUS = (RING_SIZE - RING_STROKE) / 2;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

export const programTabId = (key: string) => `program-tab-${key}`;
export const programPanelId = (key: string) => `program-panel-${key}`;

const TabList = styled.div`
  position: sticky;
  top: 0;
  z-index: 1000; /* above the sticky rule headers scrolling beneath it */
  display: flex;
  align-items: stretch;
  flex-shrink: 0;
  overflow-x: auto;
  scrollbar-width: thin;
  background: #ffffff;
  border-bottom: 1px solid #d8deef;
`;

const Tab = styled.button<{
  $kind: ProgramKind;
  $isActive: boolean;
  $scrolls: boolean;
}>`
  flex: ${(props) => (props.$scrolls ? "0 0 auto" : "1 1 0")};
  min-width: ${(props) => (props.$scrolls ? "9rem" : "0")};
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  padding: 0.55rem 0.7rem 0.65rem;
  border: none;
  border-bottom: 2px solid
    ${(props) =>
      props.$isActive ? `var(--program-${props.$kind})` : "transparent"};
  border-radius: 0;
  background: transparent;
  text-align: left;
  color: ${(props) =>
    props.$isActive ? "var(--primary-color-ultra-dark)" : "#6b7190"};
  transition: color 150ms ease, border-color 150ms ease, background 150ms ease;

  &:hover {
    color: var(--primary-color-ultra-dark);
    background: ${(props) =>
      props.$isActive ? "transparent" : "rgba(197, 210, 246, 0.28)"};
  }

  &:focus-visible {
    outline: 2px solid var(--primary-color-xx-dark);
    outline-offset: -2px;
  }
`;

const TabCopy = styled.span`
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  flex: 1;
  min-width: 0;
`;

const TabName = styled.span<{ $isActive: boolean }>`
  font-size: 0.88rem;
  font-weight: ${(props) => (props.$isActive ? 700 : 600)};
  line-height: 1.3;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`;

const TabYear = styled.span<{ $kind: ProgramKind; $isActive: boolean }>`
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: 0.01em;
  color: ${(props) =>
    props.$isActive ? "#ffffff" : `var(--program-${props.$kind})`};
  background: ${(props) =>
    props.$isActive
      ? `var(--program-${props.$kind})`
      : `var(--program-${props.$kind}-bg)`};
`;

const Ring = styled.span`
  position: relative;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: ${RING_SIZE}px;
  height: ${RING_SIZE}px;

  svg {
    position: absolute;
    inset: 0;
  }
`;

const RingLabel = styled.span`
  position: relative;
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1;
  color: var(--primary-color-ultra-dark);
`;

const ProgressRing = ({
  percent,
  kind,
  isActive,
  animate,
}: {
  percent: number;
  kind: ProgramKind;
  isActive: boolean;
  animate: boolean;
}) => (
  <Ring aria-hidden>
    <svg
      width={RING_SIZE}
      height={RING_SIZE}
      viewBox={`0 0 ${RING_SIZE} ${RING_SIZE}`}
    >
      <circle
        cx={RING_SIZE / 2}
        cy={RING_SIZE / 2}
        r={RING_RADIUS}
        fill="none"
        strokeWidth={RING_STROKE}
        stroke="var(--primary-color-dark)"
      />
      <circle
        cx={RING_SIZE / 2}
        cy={RING_SIZE / 2}
        r={RING_RADIUS}
        fill="none"
        strokeWidth={RING_STROKE}
        strokeLinecap="round"
        strokeDasharray={RING_CIRCUMFERENCE}
        strokeDashoffset={RING_CIRCUMFERENCE * (1 - percent / 100)}
        transform={`rotate(-90 ${RING_SIZE / 2} ${RING_SIZE / 2})`}
        style={{
          stroke: isActive
            ? `var(--program-${kind})`
            : "var(--primary-color-xxx-dark)",
          transition: animate ? "stroke-dashoffset 250ms ease" : "none",
        }}
      />
    </svg>
    <RingLabel>{percent}</RingLabel>
  </Ring>
);

interface ProgramTabsProps {
  tabs: ProgramTab[];
  activeKey: string;
  onSelect: (key: string) => void;
  loaded: boolean; // whether progress reflects the plan's courses yet
}

const ProgramTabs = forwardRef<HTMLDivElement, ProgramTabsProps>(
  ({ tabs, activeKey, onSelect, loaded }, ref) => {
    const scrolls = tabs.length > MAX_TABS_WITH_FULL_NAMES;

    // Every ring reads 0 until the courses load, and that first jump shouldn't animate.
    const wasLoaded = useRef(false);
    useEffect(() => {
      wasLoaded.current = loaded;
    });

    const activeTabRef = useRef<HTMLButtonElement>(null);
    useEffect(() => {
      activeTabRef.current?.scrollIntoView({
        block: "nearest",
        inline: "nearest",
      });
    }, [activeKey]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
      const index = tabs.findIndex((tab) => tab.key === activeKey);
      const targets: { [key: string]: number } = {
        ArrowLeft: (index - 1 + tabs.length) % tabs.length,
        ArrowRight: (index + 1) % tabs.length,
        Home: 0,
        End: tabs.length - 1,
      };
      if (!(e.key in targets)) return;
      e.preventDefault();
      const next = tabs[targets[e.key]];
      onSelect(next.key);
      document.getElementById(programTabId(next.key))?.focus();
    };

    return (
      <TabList
        ref={ref}
        role="tablist"
        aria-label="Degrees, majors and minors"
        onKeyDown={handleKeyDown}
      >
        {tabs.map((tab) => {
          const isActive = tab.key === activeKey;
          const percent = Math.round(tab.progress * 100);
          return (
            <Tab
              key={tab.key}
              ref={isActive ? activeTabRef : undefined}
              id={programTabId(tab.key)}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={programPanelId(tab.key)}
              aria-label={`${tab.title}, ${tab.year}, ${percent}% complete`}
              tabIndex={isActive ? 0 : -1}
              title={`${tab.title} · ${tab.year} · ${percent}%`}
              $kind={tab.kind}
              $isActive={isActive}
              $scrolls={scrolls}
              onClick={() => onSelect(tab.key)}
            >
              <TabCopy>
                <TabName $isActive={isActive}>
                  {scrolls ? tab.code : tab.title}
                </TabName>
                <TabYear $kind={tab.kind} $isActive={isActive}>
                  {tab.year}
                </TabYear>
              </TabCopy>
              <ProgressRing
                percent={percent}
                kind={tab.kind}
                isActive={isActive}
                animate={wasLoaded.current}
              />
            </Tab>
          );
        })}
      </TabList>
    );
  }
);

ProgramTabs.displayName = "ProgramTabs";

export default ProgramTabs;
