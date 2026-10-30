import { RefObject, useEffect, useMemo, useRef } from "react";

type ClickOutsideEvent = MouseEvent | TouchEvent;

/*
  Calls handler when a pointer goes down outside every ref in refs. The refs and the
  handler are read through a ref of their own, so callers can pass inline arrays and
  arrow functions without the document listeners being re-attached on every render.
*/
export const useOnClickOutside = (
  refs: RefObject<HTMLElement | null>[],
  handler: (event: ClickOutsideEvent) => void
) => {
  const refsRef = useRef(refs);
  const handlerRef = useRef(handler);
  refsRef.current = refs;
  handlerRef.current = handler;

  useEffect(() => {
    const listener = (event: Event) => {
      const path = event.composedPath();
      for (const ref of refsRef.current) {
        if (ref.current && path.includes(ref.current)) return;
      }
      handlerRef.current(event as ClickOutsideEvent);
    };

    document.addEventListener("mousedown", listener);
    document.addEventListener("touchstart", listener);

    return () => {
      document.removeEventListener("mousedown", listener);
      document.removeEventListener("touchstart", listener);
    };
  }, []);
};

/*
  Batches range slider changes so a search only fires once the user settles on a value.
  Drags commit when released. Keyboard steps also come through onInput but never fire
  drag events, so they commit after delay ms without another step. Anything still
  pending is committed on unmount, e.g. when the filter dropdown closes.
*/
export const useSliderCommit = <T>(commit: (value: T) => void, delay = 400) => {
  const commitRef = useRef(commit);
  commitRef.current = commit;

  const pending = useRef<{ value: T } | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const isDragging = useRef(false);

  const { flush, update, dragProps } = useMemo(() => {
    const flush = () => {
      window.clearTimeout(timer.current);
      if (pending.current) {
        const { value } = pending.current;
        pending.current = null;
        commitRef.current(value);
      }
    };

    const update = (value: T) => {
      pending.current = { value };
      window.clearTimeout(timer.current);
      if (!isDragging.current) {
        timer.current = window.setTimeout(flush, delay);
      }
    };

    const onDragStart = () => {
      isDragging.current = true;
      window.clearTimeout(timer.current);
    };

    // Clicking the track can end a drag that never reported starting, so flush either way
    const onDragEnd = () => {
      isDragging.current = false;
      flush();
    };

    return {
      flush,
      update,
      dragProps: {
        onThumbDragStart: onDragStart,
        onThumbDragEnd: onDragEnd,
        onRangeDragStart: onDragStart,
        onRangeDragEnd: onDragEnd
      }
    };
  }, [delay]);

  useEffect(() => flush, [flush]);

  return { update, dragProps };
};
