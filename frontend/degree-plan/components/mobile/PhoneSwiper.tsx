import styled from "@emotion/styled";
import React, { useEffect, useLayoutEffect, useRef } from "react";

const SLIDE_MS = 260;
const EASING = "cubic-bezier(0.32, 0.72, 0, 1)";
const LOCK_PX = 8;
// A release past this fraction of the width, or faster than this (px/ms), changes tab.
const DISTANCE_RATIO = 0.25;
const FLICK_SPEED = 0.4;

const Viewport = styled.div`
  position: relative;
  height: 100%;
  /* Clip, not hidden, so scrollIntoView in an off-screen slide can't scroll it partway over. */
  overflow: hidden;
  overflow: clip;
`;

const Slide = styled.div`
  position: absolute;
  inset: 0;
  padding: 0.5rem;
  box-sizing: border-box;
`;

const reducedMotion = () =>
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// A touch that starts in something that scrolls sideways scrolls that, not the tabs.
const inHorizontalScroller = (target: EventTarget | null, root: HTMLElement) => {
  for (let el = target as HTMLElement | null; el && el !== root; el = el.parentElement) {
    const { overflowX } = getComputedStyle(el);
    if ((overflowX === "auto" || overflowX === "scroll") && el.scrollWidth > el.clientWidth)
      return true;
  }
  return false;
};

interface PhoneSwiperProps<T extends string> {
  tabs: readonly T[];
  active: T;
  onChange: (tab: T) => void;
  panels: Record<T, React.ReactNode>;
}

// At rest the active slide is untransformed, since a transform would offset the panels'
// `position: fixed` popovers. The others stay mounted so they keep their scroll position.
const PhoneSwiper = <T extends string>({ tabs, active, onChange, panels }: PhoneSwiperProps<T>) => {
  const viewport = useRef<HTMLDivElement>(null);
  const slides = useRef<(HTMLDivElement | null)[]>([]);
  const index = tabs.indexOf(active);
  const shown = useRef(index);
  const settleTimer = useRef<ReturnType<typeof setTimeout>>();
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const place = (offset: (i: number) => string, animate: boolean) =>
    slides.current.forEach((slide, i) => {
      if (!slide) return;
      slide.style.transition = animate ? `transform ${SLIDE_MS}ms ${EASING}` : "none";
      slide.style.transform = offset(i);
      slide.style.visibility = "visible";
    });

  const settle = () => {
    clearTimeout(settleTimer.current);
    settleTimer.current = undefined;
    slides.current.forEach((slide, i) => {
      if (!slide) return;
      const active = i === shown.current;
      slide.style.transition = "";
      // Off to the side as well as hidden, since descendants can set `visibility: visible`.
      slide.style.transform = active ? "" : `translateX(${(i - shown.current) * 100}%)`;
      slide.style.visibility = active ? "" : "hidden";
    });
  };

  const slideTo = (target: number) => {
    shown.current = target;
    if (reducedMotion()) return settle();
    // Commit the current positions before transitioning away from them.
    void viewport.current?.offsetWidth;
    place((i) => `translateX(${(i - target) * 100}%)`, true);
    clearTimeout(settleTimer.current);
    settleTimer.current = setTimeout(settle, SLIDE_MS);
  };

  // Visibility is set here, not as a prop, so a re-render mid-slide doesn't hide a moving slide.
  useLayoutEffect(() => {
    if (index === shown.current) {
      if (!settleTimer.current) settle();
      return;
    }
    place((i) => `translateX(${(i - shown.current) * 100}%)`, false);
    slideTo(index);
  }, [index]);

  useEffect(() => () => clearTimeout(settleTimer.current), []);

  useEffect(() => {
    const root = viewport.current;
    if (!root) return undefined;
    let start: { x: number; y: number } | null = null;
    let axis: "x" | "y" | null = null;
    let dx = 0;
    let last = { x: 0, t: 0, v: 0 };

    const onStart = (e: TouchEvent) => {
      if (e.touches.length !== 1 || inHorizontalScroller(e.target, root)) {
        start = null;
        return;
      }
      const { clientX: x, clientY: y } = e.touches[0];
      start = { x, y };
      axis = null;
      dx = 0;
      last = { x, t: e.timeStamp, v: 0 };
    };

    const onMove = (e: TouchEvent) => {
      if (!start || axis === "y") return;
      const { clientX: x, clientY: y } = e.touches[0];
      if (!axis) {
        const ax = Math.abs(x - start.x);
        const ay = Math.abs(y - start.y);
        if (Math.max(ax, ay) < LOCK_PX) return;
        axis = ax > ay ? "x" : "y";
        if (axis === "y") return;
        clearTimeout(settleTimer.current);
      }
      e.preventDefault();
      const dt = e.timeStamp - last.t;
      if (dt > 0) last = { x, t: e.timeStamp, v: (x - last.x) / dt };
      dx = x - start.x;
      const atEdge =
        (shown.current === 0 && dx > 0) || (shown.current === tabs.length - 1 && dx < 0);
      const offset = atEdge ? dx / 3 : dx;
      place((i) => `translateX(calc(${(i - shown.current) * 100}% + ${offset}px))`, false);
    };

    const onEnd = () => {
      if (!start || axis !== "x") {
        start = null;
        return;
      }
      start = null;
      const width = root.clientWidth || 1;
      const flick = Math.abs(last.v) > FLICK_SPEED && Math.sign(last.v) === Math.sign(dx);
      const step = Math.abs(dx) > width * DISTANCE_RATIO || flick ? -Math.sign(dx) : 0;
      const target = Math.min(tabs.length - 1, Math.max(0, shown.current + step));
      const from = shown.current;
      slideTo(target);
      if (target !== from) onChangeRef.current(tabs[target]);
    };

    root.addEventListener("touchstart", onStart, { passive: true });
    root.addEventListener("touchmove", onMove, { passive: false });
    root.addEventListener("touchend", onEnd);
    root.addEventListener("touchcancel", onEnd);
    return () => {
      root.removeEventListener("touchstart", onStart);
      root.removeEventListener("touchmove", onMove);
      root.removeEventListener("touchend", onEnd);
      root.removeEventListener("touchcancel", onEnd);
    };
  }, [tabs]);

  return (
    <Viewport
      ref={viewport}
      onScroll={(e) => {
        e.currentTarget.scrollLeft = 0;
        e.currentTarget.scrollTop = 0;
      }}
    >
      {tabs.map((tab, i) => (
        <Slide
          key={tab}
          ref={(el) => {
            slides.current[i] = el;
          }}
          aria-hidden={i !== index || undefined}
        >
          {panels[tab]}
        </Slide>
      ))}
    </Viewport>
  );
};

export default PhoneSwiper;
