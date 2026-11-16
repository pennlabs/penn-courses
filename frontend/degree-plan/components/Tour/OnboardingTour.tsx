import styled from "@emotion/styled";
import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

/**
 * A guided tour of the degree plan page. Each step points at an element marked with
 * `data-tour="<target>"` (see `tourTarget`), so components only need an attribute, not a ref.
 * Steps whose target isn't on the page when the tour opens are skipped.
 */

type Placement = "top" | "bottom" | "left" | "right" | "center";

interface TourStep {
  target?: string; // no target: a centered card
  title: string;
  body: React.ReactNode;
  placements?: Placement[]; // tried in order; the first that fits on screen wins
}

export const tourTarget = (name: string) => ({ "data-tour": name });

const WELCOME: TourStep = {
  title: "Welcome to Penn Degree Plan!",
  body:
    "Plan all four years at Penn in one place: lay out your semesters, track your degree " +
    "requirements, and find courses to fill them. Here's a quick look around.",
};

const REPLAY: TourStep = {
  target: "replay-tour",
  title: "Need a refresher?",
  body: "You can replay this tour anytime from here.",
  placements: ["bottom", "left"],
};

const DESKTOP_STEPS: TourStep[] = [
  WELCOME,
  {
    target: "plan-panel",
    title: "Your plan",
    body:
      "Each card is a semester. Past semesters are gray, the current one is blue, and future " +
      "ones are white. Drag courses between semesters, or in from your requirements and the dock.",
    placements: ["right", "left", "center"],
  },
  {
    target: "plan-select",
    title: "Switch plans",
    body: "Keep more than one plan. Use this menu to switch between them, or to create, copy, rename, or delete one.",
    placements: ["bottom", "right"],
  },
  {
    target: "plan-actions",
    title: "Stats and semesters",
    body:
      "Show or hide course stats (quality, difficulty, and workload). Click Edit to add or remove semesters.",
    placements: ["bottom", "left"],
  },
  {
    target: "requirements-panel",
    title: "Requirements",
    body:
      "Everything your degree requires, with a tab for each major or minor. Open a requirement to " +
      "see the courses that satisfy it, then drag one into a semester.",
    placements: ["left", "right", "center"],
  },
  {
    target: "edit-programs",
    title: "Change your programs",
    body: "Add or remove majors, minors, and other programs here.",
    placements: ["bottom", "left"],
  },
  {
    target: "column-toggles",
    title: "Arrange your workspace",
    body: "Show or hide the Plan and Requirements columns. Drag the line between columns to resize them.",
    placements: ["bottom", "left"],
  },
  {
    target: "dock",
    title: "The dock",
    body: "Not sure where a course fits yet? Drop it in the dock to keep it for later.",
    placements: ["top"],
  },
  {
    target: "add-course",
    title: "Find courses",
    body: "Search the whole catalog. Results open in a column beside your plan, and you can drag them anywhere.",
    placements: ["top", "right"],
  },
  REPLAY,
];

const PHONE_STEPS: TourStep[] = [
  WELCOME,
  {
    target: "phone-tab-plan",
    title: "Your plan",
    body:
      "A card for each semester. Past semesters are gray, the current one is blue, and future " +
      "ones are white. Swipe sideways or use these tabs to move between sections.",
    placements: ["top"],
  },
  {
    target: "phone-tab-requirements",
    title: "Requirements",
    body: "Everything your degree requires, with a tab for each major or minor.",
    placements: ["top"],
  },
  {
    target: "phone-tab-search",
    title: "Add courses",
    body: "Search the whole catalog and add courses to a semester.",
    placements: ["top"],
  },
  {
    target: "phone-tab-docked",
    title: "Docked courses",
    body: "Courses you've saved for later, before you've picked a semester.",
    placements: ["top"],
  },
  REPLAY,
];

const findTarget = (step: TourStep): HTMLElement | null =>
  step.target ? document.querySelector<HTMLElement>(`[data-tour="${step.target}"]`) : null;

const VIEWPORT_MARGIN = 16;
const GAP = 14; // between the highlighted element and the card
const SPOTLIGHT_PADDING = 6;

type Box = { top: number; left: number; width: number; height: number };

// The visible part of the target, so a panel taller than the window doesn't push the card off screen.
const visibleBox = (rect: DOMRect): Box => {
  const top = Math.max(rect.top - SPOTLIGHT_PADDING, 0);
  const left = Math.max(rect.left - SPOTLIGHT_PADDING, 0);
  const bottom = Math.min(rect.bottom + SPOTLIGHT_PADDING, window.innerHeight);
  const right = Math.min(rect.right + SPOTLIGHT_PADDING, window.innerWidth);
  return { top, left, width: Math.max(right - left, 0), height: Math.max(bottom - top, 0) };
};

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), Math.max(min, max));

const placeCard = (
  target: Box | null,
  card: { width: number; height: number },
  placements: Placement[]
): { top: number; left: number } => {
  const maxLeft = window.innerWidth - card.width - VIEWPORT_MARGIN;
  const maxTop = window.innerHeight - card.height - VIEWPORT_MARGIN;
  const centered = {
    top: clamp((window.innerHeight - card.height) / 2, VIEWPORT_MARGIN, maxTop),
    left: clamp((window.innerWidth - card.width) / 2, VIEWPORT_MARGIN, maxLeft),
  };
  if (!target) return centered;

  const midX = target.left + target.width / 2 - card.width / 2;
  const midY = target.top + target.height / 2 - card.height / 2;
  for (const placement of placements) {
    switch (placement) {
      case "right": {
        const left = target.left + target.width + GAP;
        if (left <= maxLeft) return { left, top: clamp(midY, VIEWPORT_MARGIN, maxTop) };
        break;
      }
      case "left": {
        const left = target.left - GAP - card.width;
        if (left >= VIEWPORT_MARGIN) return { left, top: clamp(midY, VIEWPORT_MARGIN, maxTop) };
        break;
      }
      case "bottom": {
        const top = target.top + target.height + GAP;
        if (top <= maxTop) return { top, left: clamp(midX, VIEWPORT_MARGIN, maxLeft) };
        break;
      }
      case "top": {
        const top = target.top - GAP - card.height;
        if (top >= VIEWPORT_MARGIN) return { top, left: clamp(midX, VIEWPORT_MARGIN, maxLeft) };
        break;
      }
      case "center":
        return {
          top: clamp(midY, VIEWPORT_MARGIN, maxTop),
          left: clamp(midX, VIEWPORT_MARGIN, maxLeft),
        };
    }
  }
  return centered;
};

const Z_INDEX = 100000; // above popovers and the notification menu, below the login modal

// Catches clicks so the page can't be changed underneath the tour.
const ClickShield = styled.div`
  position: fixed;
  inset: 0;
  z-index: ${Z_INDEX};
`;

const Backdrop = styled.div`
  position: fixed;
  inset: 0;
  z-index: ${Z_INDEX};
  background: rgba(30, 32, 60, 0.55);
  pointer-events: none;
`;

// A hole in the backdrop: its huge shadow darkens everything around the highlighted element.
const Spotlight = styled.div`
  position: fixed;
  z-index: ${Z_INDEX};
  border-radius: 12px;
  box-shadow: 0 0 0 200vmax rgba(30, 32, 60, 0.55);
  pointer-events: none;
  transition: top 200ms ease, left 200ms ease, width 200ms ease, height 200ms ease;

  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
`;

const Card = styled.div`
  position: fixed;
  z-index: ${Z_INDEX + 1};
  width: min(360px, calc(100vw - ${2 * VIEWPORT_MARGIN}px));
  /* Scrolls on short screens so the buttons stay reachable. dvh excludes mobile browser chrome. */
  max-height: calc(100vh - ${2 * VIEWPORT_MARGIN}px);
  max-height: calc(100dvh - ${2 * VIEWPORT_MARGIN}px);
  overflow-y: auto;
  box-sizing: border-box;
  padding: 1.25rem 1.25rem 1rem;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 12px 32px rgba(30, 32, 60, 0.25);
  color: var(--modal-text-color);
  font-family: inherit;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 0.6rem;
  right: 0.6rem;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 6px;
  background: none;
  color: var(--primary-color-ultra-dark);
  font-size: 1rem;
  cursor: pointer;

  &:hover {
    background: var(--primary-color-light);
  }
`;

const Mascot = styled.img`
  display: block;
  width: 9rem;
  margin: 0.25rem auto 0.75rem;
`;

const Title = styled.h2`
  margin: 0 2rem 0.5rem 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
`;

const Body = styled.p`
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.45;
`;

const Footer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1.1rem;
`;

const Progress = styled.span`
  font-size: 0.8rem;
  color: var(--primary-color-extra-dark);
  font-variant-numeric: tabular-nums;
`;

const Buttons = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const Button = styled.button<{ $primary?: boolean }>`
  min-height: 2rem;
  padding: 0.35rem 0.9rem;
  border-radius: 6px;
  border: 1px solid ${(props) => (props.$primary ? "var(--modal-button-color)" : "var(--primary-color-dark)")};
  background: ${(props) => (props.$primary ? "var(--modal-button-color)" : "#ffffff")};
  color: ${(props) => (props.$primary ? "#ffffff" : "var(--primary-color-ultra-dark)")};
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    filter: brightness(0.96);
  }
`;

interface OnboardingTourProps {
  isPhone: boolean;
  onFinish: () => void; // closing early counts as finishing
}

const OnboardingTour = ({ isPhone, onFinish }: OnboardingTourProps) => {
  // Chosen once the page has rendered with the tour open (it may have just reopened a column),
  // then fixed so the step count doesn't shift underneath the reader. Crossing the phone
  // breakpoint swaps the whole layout, so that starts the tour over with the other steps.
  const [steps, setSteps] = useState<TourStep[]>([]);
  const [index, setIndex] = useState(0);
  useLayoutEffect(() => {
    setSteps(
      (isPhone ? PHONE_STEPS : DESKTOP_STEPS).filter((step) => !step.target || findTarget(step))
    );
    setIndex(0);
  }, [isPhone]);
  const step: TourStep | undefined = steps[index];
  const isFirst = index === 0;
  const isLast = index === steps.length - 1;

  const [targetBox, setTargetBox] = useState<Box | null>(null);
  const [cardPosition, setCardPosition] = useState<{ top: number; left: number } | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const primaryButtonRef = useRef<HTMLButtonElement>(null);

  const next = useCallback(() => (isLast ? onFinish() : setIndex((i) => i + 1)), [isLast, onFinish]);
  const back = useCallback(() => setIndex((i) => Math.max(i - 1, 0)), []);

  // Follow the target as it scrolls, resizes, or finishes loading.
  useLayoutEffect(() => {
    const target = step && findTarget(step);
    if (!target) {
      setTargetBox(null);
      return;
    }
    target.scrollIntoView({ block: "nearest", inline: "nearest" });
    const update = () => setTargetBox(visibleBox(target.getBoundingClientRect()));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(target);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [step]);

  // Re-placed when the card itself resizes too, e.g. once the welcome image loads.
  useLayoutEffect(() => {
    const card = cardRef.current;
    if (!card || !step) return;
    const place = () => {
      const { width, height } = card.getBoundingClientRect();
      setCardPosition(placeCard(targetBox, { width, height }, step.placements ?? ["bottom"]));
    };
    place();
    const observer = new ResizeObserver(place);
    observer.observe(card);
    window.addEventListener("resize", place);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", place);
    };
  }, [targetBox, step]);

  useEffect(() => {
    primaryButtonRef.current?.focus();
  }, [index, steps]);

  // Read during the first render, before the tour moves focus, and given back when it closes.
  const [returnFocusTo] = useState(() => document.activeElement);
  useEffect(
    () => () => {
      if (returnFocusTo instanceof HTMLElement && returnFocusTo.isConnected) returnFocusTo.focus();
    },
    [returnFocusTo]
  );

  useEffect(() => {
    // Keeps Tab and Shift+Tab inside the card, as the page behind it can't be used.
    const trapTab = (e: KeyboardEvent) => {
      const focusable = Array.from(
        cardRef.current?.querySelectorAll<HTMLElement>("button:not([disabled])") ?? []
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      const inside = !!active && cardRef.current!.contains(active);
      if (e.shiftKey && (active === first || !inside)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (active === last || !inside)) {
        e.preventDefault();
        first.focus();
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Tab") return trapTab(e);
      if (e.key === "Escape") onFinish();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") back();
      else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [next, back, onFinish]);

  if (!step) return null;

  return (
    <>
      <ClickShield />
      {targetBox ? <Spotlight style={targetBox} /> : <Backdrop />}
      <Card
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-tour-title"
        aria-describedby="onboarding-tour-body"
        // Measured before it's placed, so hide it until then.
        style={cardPosition ?? { top: 0, left: 0, visibility: "hidden" }}
      >
        <CloseButton type="button" aria-label="Close tour" onClick={onFinish}>
          <i className="fas fa-times" aria-hidden />
        </CloseButton>
        {isFirst && <Mascot src="pdp-porcupine.svg" alt="" />}
        <Title id="onboarding-tour-title">{step.title}</Title>
        <Body id="onboarding-tour-body">{step.body}</Body>
        <Footer>
          <Progress aria-label={`Step ${index + 1} of ${steps.length}`}>
            {index + 1} / {steps.length}
          </Progress>
          <Buttons>
            {isFirst ? (
              <Button type="button" onClick={onFinish}>
                Skip
              </Button>
            ) : (
              <Button type="button" onClick={back}>
                Back
              </Button>
            )}
            <Button type="button" $primary ref={primaryButtonRef} onClick={next}>
              {isFirst ? "Start tour" : isLast ? "Done" : "Next"}
            </Button>
          </Buttons>
        </Footer>
      </Card>
    </>
  );
};

export default OnboardingTour;
