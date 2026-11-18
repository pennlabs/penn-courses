import React, {
  ReactNode,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { keyframes } from "@emotion/react";
import styled from "@emotion/styled";
import useStickyState from "@/hooks/stickyState";

const MIN_COLUMN_PERCENT = 22;
const KEYBOARD_STEP_PERCENT = 2;
const KEYBOARD_DIRECTIONS: { [key: string]: number } = {
  ArrowLeft: -1,
  ArrowRight: 1,
};
const GUTTER_WIDTH_PX = 8;
const RESIZING_BODY_CLASS = "is-resizing-columns";

const Container = styled.div`
  display: flex;
  flex-direction: row;
  align-items: stretch;
  width: 100%;
  height: 100%;
`;

const collapsed = `
  flex-grow: 0;
  opacity: 0;
  transform: translateX(12px);
`;
const columnIn = keyframes`
  from { ${collapsed} }
`;
const columnOut = keyframes`
  to { ${collapsed} }
`;
const SLIDE = "280ms cubic-bezier(0.2, 0.8, 0.2, 1)";

const Column = styled.div`
  min-width: 0;
  height: 100%;

  &.column-enter,
  &.column-leave {
    overflow: hidden;
  }
  &.column-enter {
    animation: ${columnIn} ${SLIDE};
  }
  &.column-leave {
    animation: ${columnOut} ${SLIDE} forwards;
    pointer-events: none;
  }
`;

const Gutter = styled.div`
  flex: 0 0 ${GUTTER_WIDTH_PX}px;
  position: relative;
  cursor: col-resize;
  touch-action: none;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: 50%;
    width: 2px;
    transform: translateX(-50%);
    border-radius: 1px;
    transition: background 120ms ease;
  }

  &:hover::before,
  &:focus-visible::before,
  &[data-active="true"]::before {
    background: var(--primary-color-xx-dark);
  }

  &:focus-visible {
    outline: none;
  }
`;

const EmptyState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 2rem;
  text-align: center;
  font-weight: 500;
  color: var(--primary-color-xxx-dark);
`;

export interface SplitColumn {
  id: string;
  label: string; // names the gutter to its left for screen readers
  visible: boolean;
  content: ReactNode;
}

interface SplitColumnsProps {
  columns: SplitColumn[];
  storageKey: string;
  /** Widths in percent for each combination of visible columns, keyed by their ids joined by "+". */
  defaultWidths: { [layout: string]: number[] };
  emptyState?: ReactNode;
}

const isValidWidths = (widths: unknown, count: number): widths is number[] =>
  Array.isArray(widths) &&
  widths.length === count &&
  widths.every(
    (width) => typeof width === "number" && width >= MIN_COLUMN_PERCENT
  ) &&
  Math.abs(widths.reduce((sum, width) => sum + width, 0) - 100) < 0.5;

/** Moves the boundary after column `index`, leaving every other column's width alone. */
const resizePair = (widths: number[], index: number, nextWidth: number) => {
  const pair = widths[index] + widths[index + 1];
  const clamped = Math.min(
    pair - MIN_COLUMN_PERCENT,
    Math.max(MIN_COLUMN_PERCENT, nextWidth)
  );
  const next = [...widths];
  next[index] = clamped;
  next[index + 1] = pair - clamped;
  return next;
};

/**
 * Resizable columns that can each be shown or hidden. A hidden column stays mounted when its
 * `content` is still passed, so toggling it doesn't lose state such as edit mode or scroll position.
 * Each combination of visible columns remembers its own widths.
 */
const SplitColumns = ({
  columns,
  storageKey,
  defaultWidths,
  emptyState,
}: SplitColumnsProps) => {
  const visible = columns.filter((column) => column.visible);
  const layout = visible.map((column) => column.id).join("+");

  const [storedWidths, setStoredWidths] = useStickyState<{
    [layout: string]: number[];
  }>(storageKey, {});
  // Widths mid-drag, saved once the drag ends so that storage isn't written on every pointer move.
  const [dragWidths, setDragWidths] = useState<number[] | null>(null);
  const [activeGutter, setActiveGutter] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // A hiding column keeps its last width and content until it has slid away.
  const shown = useRef<Set<string> | null>(null);
  const lastGrow = useRef<{ [id: string]: number }>({});
  const lastContent = useRef<{ [id: string]: ReactNode }>({});
  const [sliding, setSliding] = useState<{ [id: string]: "enter" | "leave" }>(
    {}
  );
  useLayoutEffect(() => {
    const now = new Set(visible.map((column) => column.id));
    const previous = shown.current;
    shown.current = now;
    if (!previous) return;
    const changes: { [id: string]: "enter" | "leave" } = {};
    now.forEach((id) => {
      if (!previous.has(id)) changes[id] = "enter";
    });
    previous.forEach((id) => {
      if (!now.has(id)) changes[id] = "leave";
    });
    if (Object.keys(changes).length)
      setSliding((current) => ({ ...current, ...changes }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layout]);
  const finishSliding = (id: string) =>
    setSliding((current) => {
      if (!(id in current)) return current;
      const rest = { ...current };
      delete rest[id];
      return rest;
    });
  // Also checked against the last render, so a column that was just hidden keeps its content
  // mounted in the render before the effect above has marked it.
  const isLeaving = (column: SplitColumn) =>
    !column.visible &&
    (sliding[column.id] === "leave" || !!shown.current?.has(column.id));
  const leaving = columns.filter(isLeaving);

  const committedWidths =
    [storedWidths?.[layout], defaultWidths[layout]].find((candidate) =>
      isValidWidths(candidate, visible.length)
    ) ?? visible.map(() => 100 / visible.length);
  const widths = dragWidths ?? committedWidths;

  const commit = (next: number[]) =>
    setStoredWidths({ ...storedWidths, [layout]: next });

  useEffect(() => {
    if (activeGutter === null) return undefined;
    let latestDragWidths: number[] | null = null;

    const handlePointerMove = (e: PointerEvent) => {
      const container = containerRef.current;
      if (!container) return;
      e.preventDefault();
      const rect = container.getBoundingClientRect();
      const available = rect.width - GUTTER_WIDTH_PX * (visible.length - 1);
      const boundary =
        ((e.clientX - rect.left - GUTTER_WIDTH_PX * activeGutter) / available) *
        100;
      const before = committedWidths
        .slice(0, activeGutter)
        .reduce((sum, width) => sum + width, 0);
      latestDragWidths = resizePair(
        committedWidths,
        activeGutter,
        boundary - before
      );
      setDragWidths(latestDragWidths);
    };

    const handlePointerUp = () => {
      if (latestDragWidths) commit(latestDragWidths);
      setDragWidths(null);
      setActiveGutter(null);
    };

    document.body.classList.add(RESIZING_BODY_CLASS);
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
    return () => {
      document.body.classList.remove(RESIZING_BODY_CLASS);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    };
    // Only a new drag restarts this: the committed widths and layout can't change during one.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeGutter]);

  const handleGutterKeyDown = (e: React.KeyboardEvent, index: number) => {
    const direction = KEYBOARD_DIRECTIONS[e.key];
    if (!direction) return;
    e.preventDefault();
    commit(
      resizePair(
        widths,
        index,
        widths[index] + direction * KEYBOARD_STEP_PERCENT
      )
    );
  };

  let visibleIndex = -1;
  return (
    <Container ref={containerRef}>
      {!visible.length && !leaving.length && (
        <EmptyState>{emptyState}</EmptyState>
      )}
      {/* A flat, keyed list: each Column keeps its identity when shown or hidden, so stays mounted. */}
      {columns.flatMap((column) => {
        if (column.visible && column.content)
          lastContent.current[column.id] = column.content;
        if (isLeaving(column)) {
          return [
            <Column
              key={column.id}
              className="column-leave"
              aria-hidden
              style={{ flex: `${lastGrow.current[column.id] ?? 0} 1 0` }}
              onAnimationEnd={(e) => {
                if (e.target === e.currentTarget) finishSliding(column.id);
              }}
            >
              {column.content || lastContent.current[column.id]}
            </Column>,
          ];
        }
        if (!column.visible) {
          return [
            <Column key={column.id} style={{ display: "none" }}>
              {column.content}
            </Column>,
          ];
        }
        visibleIndex += 1;
        const gutterIndex = visibleIndex - 1;
        lastGrow.current[column.id] = widths[visibleIndex];
        const columnElement = (
          <Column
            key={column.id}
            className={
              sliding[column.id] === "enter" ? "column-enter" : undefined
            }
            style={{ flex: `${widths[visibleIndex]} 1 0` }}
            onAnimationEnd={(e) => {
              if (e.target === e.currentTarget) finishSliding(column.id);
            }}
          >
            {column.content}
          </Column>
        );
        if (gutterIndex < 0) return [columnElement];
        return [
          <Gutter
            key={`gutter-${column.id}`}
            role="separator"
            tabIndex={0}
            aria-orientation="vertical"
            aria-label={`Resize ${column.label} column`}
            aria-valuemin={MIN_COLUMN_PERCENT}
            aria-valuemax={Math.round(
              widths[gutterIndex] + widths[gutterIndex + 1] - MIN_COLUMN_PERCENT
            )}
            aria-valuenow={Math.round(widths[gutterIndex])}
            data-active={activeGutter === gutterIndex}
            onPointerDown={(e) => {
              e.preventDefault();
              setActiveGutter(gutterIndex);
            }}
            onKeyDown={(e) => handleGutterKeyDown(e, gutterIndex)}
          />,
          columnElement,
        ];
      })}
    </Container>
  );
};

export default SplitColumns;
