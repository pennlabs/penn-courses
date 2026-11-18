import React, { useLayoutEffect, useRef, useState } from "react";
import styled from "@emotion/styled";

const DURATION_MS = 200;

export const Chevron = styled.i<{ $degrees: number }>`
  transform: rotate(${(props) => props.$degrees}deg);
  transition: transform ${DURATION_MS}ms ease;

  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
`;

export const reducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Only the wrapper's height animates; the content keeps its own height, so the rules inside
 * are not laid out again every frame. It clips with `overflow: clip` rather than `hidden`,
 * which would make the wrapper a scroll container and jolt the sticky rule headers inside.
 */
const Collapse = ({ open, children }: { open: boolean; children: React.ReactNode }) => {
  const [mounted, setMounted] = useState(open);
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  // Animates on a change, not on mounting, even when Strict Mode runs the effect twice.
  const lastOpen = useRef(open);

  if (open && !mounted) setMounted(true);

  useLayoutEffect(() => {
    if (lastOpen.current === open) return;
    lastOpen.current = open;
    const outer = outerRef.current;
    const inner = innerRef.current;
    if (!outer || !inner) return;

    const finish = () => {
      outer.style.transition = "";
      if (open) {
        outer.style.height = "";
        outer.style.overflow = "";
      } else {
        setMounted(false);
      }
    };
    if (reducedMotion()) {
      finish();
      return;
    }

    const animating = outer.style.height !== "";
    const from = animating ? outer.getBoundingClientRect().height : open ? 0 : inner.offsetHeight;
    outer.style.overflow = "hidden"; // for browsers without clip
    outer.style.overflow = "clip";
    outer.style.transition = "";
    outer.style.height = `${from}px`;
    outer.getBoundingClientRect(); // commit the start height before transitioning from it
    outer.style.transition = `height ${DURATION_MS}ms ease`;
    outer.style.height = `${open ? inner.offsetHeight : 0}px`;

    const done = setTimeout(finish, DURATION_MS);
    return () => clearTimeout(done);
  }, [open]);

  if (!mounted) return null;
  return (
    <div ref={outerRef}>
      <div ref={innerRef} style={{ display: "flow-root" }}>
        {children}
      </div>
    </div>
  );
};

export default Collapse;
