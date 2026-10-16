import React, { useRef, useState } from "react";
import styled from "styled-components";

interface CollapseProps {
  open: boolean;
  children: React.ReactNode;
  unclipped?: boolean;
  onOpenComplete?: () => void;
  className?: string;
}

const Outer = styled.div`
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows ${({ theme }) => theme.motion.duration.slow}
    ${({ theme }) => theme.motion.ease.emphasized};

  &[data-open="true"] {
    grid-template-rows: 1fr;
  }
`;

const Inner = styled.div<{ $clip: boolean }>`
  min-height: 0;
  overflow: ${({ $clip }) => ($clip ? "clip" : "visible")};
  opacity: 0;
  transition: opacity ${({ theme }) => theme.motion.duration.md}
    ${({ theme }) => theme.motion.ease.standard};

  [data-open="true"] > & {
    opacity: 1;
  }
`;

const Collapse = ({
  open,
  children,
  unclipped = false,
  onOpenComplete,
  className,
}: CollapseProps) => {
  const outerRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(open);
  const [moving, setMoving] = useState(false);
  const prevOpen = useRef(open);

  if (prevOpen.current !== open) {
    prevOpen.current = open;
    setMoving(true);
  }

  if (open && !mounted) setMounted(true);

  const handleTransitionEnd = (event: React.TransitionEvent<HTMLDivElement>) => {
    // Ignore transitions bubbling up from the content, including a nested Collapse.
    if (
      event.target !== outerRef.current ||
      event.propertyName !== "grid-template-rows"
    ) {
      return;
    }
    setMoving(false);
    if (open) onOpenComplete?.();
    else setMounted(false);
  };

  // Clip the content while it is moving or closed, unless the caller has requested
  const clip = !unclipped && (moving || !open);

  const inertProps = open ? {} : ({ inert: "" } as React.HTMLAttributes<HTMLDivElement>);

  return (
    <Outer
      ref={outerRef}
      data-open={open}
      onTransitionEnd={handleTransitionEnd}
      className={className}
    >
      <Inner $clip={clip} {...inertProps}>
        {mounted ? children : null}
      </Inner>
    </Outer>
  );
};

export default Collapse;
