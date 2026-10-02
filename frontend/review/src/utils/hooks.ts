import { RefObject, useEffect, useRef } from "react";

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
