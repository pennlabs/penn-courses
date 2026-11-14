import { useEffect, useLayoutEffect, useRef, useState } from "react";
import styled from "@emotion/styled";
import { ConnectDragPreview, useDragDropManager, useDragLayer } from "react-dnd";
import { getEmptyImage } from "react-dnd-html5-backend";
import { ItemTypes } from "../Dock/dnd/constants";
import { DnDCourse } from "@/types";

const COURSE_TYPES = new Set<string | symbol>([
  ItemTypes.COURSE_IN_PLAN,
  ItemTypes.COURSE_IN_REQ,
  ItemTypes.COURSE_IN_DOCK,
  ItemTypes.COURSE_IN_EXPAND,
  ItemTypes.COURSE_IN_SEARCH,
]);

// The browser's drag image is a snapshot of whatever was grabbed; CourseDragLayer draws one card instead.
export const useCourseDragPreview = (preview: ConnectDragPreview) => {
  useEffect(() => {
    preview(getEmptyImage(), { captureDraggingState: true });
  }, [preview]);
};

const Layer = styled.div`
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 10000;
`;

const Card = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  padding: 0.5rem 0.9rem;
  border-radius: 9px;
  background-color: #ffffff;
  box-shadow: rgba(0, 0, 0, 0.12) 0px 8px 16px, rgba(129, 154, 225, 0.55) 0px 0px 0px 1.5px;
  font-size: 1rem;
  color: #363636;
  white-space: nowrap;
  /* It hangs from the pointer, so it swings about its top. */
  transform-origin: 50% 0;
  will-change: transform;
`;

// Damping is a ratio: 1 settles without overshooting, below 1 overshoots first.
const FOLLOW = { stiffness: 2400, damping: 1 };
const RETURN = { stiffness: 320, damping: 0.8 };
const SWING = { stiffness: 260, damping: 0.45 };
const POP = { stiffness: 520, damping: 0.4 };
// Stiff springs are only stable in short steps.
const SUBSTEP = 1 / 240;
const TILT_PER_SPEED = 0.012;
const MAX_TILT = 14;
const RESTING_TILT = -2;
// The browser reports the pointer only every 50ms or so during a drag, so between reports
// the card carries on at the pointer's last speed, for at most this long.
const MAX_PREDICTION_S = 0.06;
const MAX_SPEED = 3000;
const MIN_SPEED_INTERVAL_S = 0.008;
const SPEED_SMOOTHING = 0.5;
const FADE_S = 0.12;

type Spring = { value: number; velocity: number };
type Pointer = { x: number; y: number; vx: number; vy: number; t: number };
type Phase = "idle" | "dragging" | "returning";

const step = (spring: Spring, target: number, { stiffness, damping }: typeof FOLLOW, dt: number) => {
  const force = stiffness * (target - spring.value) - 2 * damping * Math.sqrt(stiffness) * spring.velocity;
  spring.velocity += force * dt;
  spring.value += spring.velocity * dt;
};

const reducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Lets a course be dropped anywhere while it's dragged. Released off a target, the browser
 * would otherwise slide its (empty) drag image home and hold the drag open until it's done;
 * a drop on nothing ends the drag at once, and the card springs home itself.
 */
const useDropAnywhere = (active: boolean) => {
  useEffect(() => {
    if (!active) return;
    // After react-dnd's own handler on window, which marks anywhere but a target "none".
    const allow = (e: DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer && e.dataTransfer.dropEffect === "none") e.dataTransfer.dropEffect = "move";
    };
    window.addEventListener("dragover", allow);
    window.addEventListener("drop", allow);
    return () => {
      window.removeEventListener("dragover", allow);
      window.removeEventListener("drop", allow);
    };
  }, [active]);
};

const CourseDragLayer = () => {
  const { item, itemType, isDragging, pointer, origin } = useDragLayer((monitor) => ({
    item: monitor.getItem() as DnDCourse | null,
    itemType: monitor.getItemType(),
    isDragging: monitor.isDragging(),
    pointer: monitor.getClientOffset(),
    origin: monitor.getInitialClientOffset(),
  }));
  const dragging = isDragging && !!item?.full_code && !!itemType && COURSE_TYPES.has(itemType);

  // react-dnd forgets whether the drag landed as soon as it ends, so note it while it lasts.
  const dropped = useRef(false);
  const manager = useDragDropManager();
  useEffect(() => {
    const monitor = manager.getMonitor();
    return monitor.subscribeToStateChange(() => {
      if (!monitor.isDragging()) return;
      dropped.current = monitor.didDrop();
    });
  }, [manager]);

  const [phase, setPhase] = useState<Phase>("idle");
  if (dragging && phase !== "dragging") {
    dropped.current = false;
    setPhase("dragging");
  } else if (!dragging && phase === "dragging") {
    setPhase(dropped.current || reducedMotion() ? "idle" : "returning");
  }
  useDropAnywhere(phase === "dragging");

  const code = useRef("");
  const home = useRef<{ x: number; y: number } | null>(null);
  if (dragging) {
    code.current = item!.full_code;
    home.current = origin;
  }

  const latest = useRef<Pointer | null>(null);
  if (dragging && pointer) {
    const now = performance.now() / 1000;
    const before = latest.current;
    if (!before) {
      latest.current = { ...pointer, vx: 0, vy: 0, t: now };
    } else if (before.x !== pointer.x || before.y !== pointer.y) {
      const dt = now - before.t;
      const clamp = (v: number) => Math.max(-MAX_SPEED, Math.min(MAX_SPEED, v));
      const blend = (old: number, moved: number) =>
        dt < MIN_SPEED_INTERVAL_S ? old : clamp(old + SPEED_SMOOTHING * (moved / dt - old));
      latest.current = {
        ...pointer,
        vx: blend(before.vx, pointer.x - before.x),
        vy: blend(before.vy, pointer.y - before.y),
        t: now,
      };
    }
  } else if (!dragging) {
    latest.current = null;
  }

  const cardRef = useRef<HTMLDivElement>(null);
  const shown = phase !== "idle";

  // Placed before it paints, so it never shows at the corner of the screen.
  useLayoutEffect(() => {
    const card = cardRef.current;
    const start = latest.current;
    if (!shown || !card || !start) return;

    const still = reducedMotion();
    const x = { value: start.x, velocity: 0 };
    const y = { value: start.y, velocity: 0 };
    const tilt = { value: RESTING_TILT, velocity: 0 };
    const scale = { value: still ? 1 : 0.8, velocity: 0 };
    let opacity = 1;

    const place = () => {
      card.style.transform =
        `translate(${x.value}px, ${y.value}px) translate(-50%, -30%) ` +
        `rotate(${tilt.value}deg) scale(${scale.value})`;
      card.style.opacity = String(opacity);
    };
    place();

    let frame = 0;
    let last = performance.now() / 1000;
    const tick = () => {
      const now = performance.now() / 1000;
      // Long gaps, like a background tab, would otherwise fling the card.
      const elapsed = Math.min(now - last, 1 / 20);
      last = now;
      const pointer = latest.current;
      const returning = !pointer;

      let goalX = x.value;
      let goalY = y.value;
      if (pointer) {
        // No report for a while means the pointer has stopped where it was last seen.
        const since = now - pointer.t;
        const ahead = since > MAX_PREDICTION_S ? 0 : since;
        goalX = pointer.x + pointer.vx * ahead;
        goalY = pointer.y + pointer.vy * ahead;
      } else if (home.current) {
        goalX = home.current.x;
        goalY = home.current.y;
      }

      if (still) {
        x.value = goalX;
        y.value = goalY;
      } else {
        for (let t = 0; t < elapsed; t += SUBSTEP) {
          const dt = Math.min(SUBSTEP, elapsed - t);
          step(x, goalX, returning ? RETURN : FOLLOW, dt);
          step(y, goalY, returning ? RETURN : FOLLOW, dt);
          const lean = Math.max(-MAX_TILT, Math.min(MAX_TILT, x.velocity * TILT_PER_SPEED));
          step(tilt, RESTING_TILT + lean, SWING, dt);
          step(scale, 1, POP, dt);
        }
      }

      if (returning) {
        const home_ = Math.hypot(goalX - x.value, goalY - y.value) < 2;
        const settled = Math.hypot(x.velocity, y.velocity) < 40;
        if (home_ && settled) opacity = Math.max(0, opacity - elapsed / FADE_S);
        if (opacity === 0) {
          setPhase("idle");
          return;
        }
      }
      place();
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [shown]);

  if (!shown) return null;
  return (
    <Layer>
      <Card ref={cardRef}>{code.current.replace("-", " ")}</Card>
    </Layer>
  );
};

export default CourseDragLayer;
