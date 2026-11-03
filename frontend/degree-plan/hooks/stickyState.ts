import { useCallback, useEffect, useState } from "react";

/**
 * useState backed by localStorage. The stored value is read after mount, so the server render and
 * the first client render agree. Writes happen in the setter rather than in an effect, which would
 * overwrite the stored value with `initial` before it had been read.
 */
function useStickyState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(initial);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored !== null) setValue(JSON.parse(stored));
    } catch {
      // Unavailable storage or a malformed value: keep the initial value.
    }
  }, [key]);

  const setStickyValue = useCallback(
    (next: T) => {
      setValue(next);
      try {
        localStorage.setItem(key, JSON.stringify(next));
      } catch {
        // Unavailable storage: the value still applies for this session.
      }
    },
    [key]
  );

  return [value, setStickyValue] as const;
}

export default useStickyState;
