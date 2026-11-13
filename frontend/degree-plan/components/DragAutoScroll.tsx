import { useEffect } from "react";
import { useDragLayer } from "react-dnd";

const EDGE = 72;
const MAX_SPEED = 18;

const pull = (pointer: number, start: number, end: number) => {
  const zone = Math.min(EDGE, (end - start) / 3);
  if (zone <= 0) return 0;
  if (pointer < start + zone) {
    return -Math.ceil(MAX_SPEED * Math.min(1, (start + zone - pointer) / zone));
  }
  if (pointer > end - zone) {
    return Math.ceil(MAX_SPEED * Math.min(1, (pointer - (end - zone)) / zone));
  }
  return 0;
};

const scrollable = (overflow: string, isRoot: boolean) =>
  isRoot ? overflow !== "hidden" : overflow === "auto" || overflow === "scroll";

// Browsers scroll during a drag themselves, but only from a sliver at the edge and slowly.
const DragAutoScroll = () => {
  const isDragging = useDragLayer((monitor) => monitor.isDragging());

  useEffect(() => {
    if (!isDragging) return;
    let pointer: { x: number; y: number } | null = null;
    let frame = 0;

    const onDragOver = (event: DragEvent) => {
      pointer = { x: event.clientX, y: event.clientY };
    };
    // No dragover arrives once the pointer is outside the window, so stop rather than keep
    // scrolling from where it was last seen.
    const onDragLeave = (event: DragEvent) => {
      if (!event.relatedTarget) pointer = null;
    };

    const step = () => {
      frame = requestAnimationFrame(step);
      if (!pointer) return;
      let element = document.elementFromPoint(pointer.x, pointer.y);
      for (; element; element = element.parentElement) {
        const isRoot = element === document.scrollingElement;
        const style = getComputedStyle(element);
        const rect = isRoot
          ? { top: 0, bottom: window.innerHeight, left: 0, right: window.innerWidth }
          : element.getBoundingClientRect();
        const dy =
          scrollable(style.overflowY, isRoot) && element.scrollHeight > element.clientHeight
            ? pull(pointer.y, rect.top, rect.bottom)
            : 0;
        const dx =
          scrollable(style.overflowX, isRoot) && element.scrollWidth > element.clientWidth
            ? pull(pointer.x, rect.left, rect.right)
            : 0;
        if (!dx && !dy) continue;
        const { scrollTop, scrollLeft } = element;
        element.scrollTop += dy;
        element.scrollLeft += dx;
        if (element.scrollTop !== scrollTop || element.scrollLeft !== scrollLeft) return;
      }
    };

    window.addEventListener("dragover", onDragOver);
    window.addEventListener("dragleave", onDragLeave);
    frame = requestAnimationFrame(step);
    return () => {
      window.removeEventListener("dragover", onDragOver);
      window.removeEventListener("dragleave", onDragLeave);
      cancelAnimationFrame(frame);
    };
  }, [isDragging]);

  return null;
};

export default DragAutoScroll;
