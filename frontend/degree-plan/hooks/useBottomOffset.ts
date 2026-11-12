import { RefObject, useEffect } from "react";

export const BOTTOM_OFFSET_VAR = "--bottom-chrome-offset";

// Publishes how far `ref`'s element reaches up from the bottom of the window, so toasts
// (see globals.css) sit above whatever is pinned there, like the phone tab bar.
const useBottomOffset = (ref: RefObject<HTMLElement>) => {
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const root = document.documentElement;
    const update = () => {
      const offset = window.innerHeight - el.getBoundingClientRect().top;
      root.style.setProperty(BOTTOM_OFFSET_VAR, `${Math.max(0, offset)}px`);
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    window.addEventListener("resize", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
      root.style.removeProperty(BOTTOM_OFFSET_VAR);
    };
  }, [ref]);
};

export default useBottomOffset;
