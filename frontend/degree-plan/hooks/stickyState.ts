import { useCallback, useEffect, useState } from "react";

/**
 * useState backed by localStorage. The stored value is read after mount, so the server render and
 * the first client render agree. Writes happen in the setter rather than in an effect, which would
 * overwrite the stored value with `initial` before it had been read. When `key` changes, a key
 * with nothing stored goes back to `initial` rather than keeping the previous key's value.
 */
function useStickyState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(initial);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(key);
      setValue(stored !== null ? JSON.parse(stored) : initial);
    } catch {
      setValue(initial); // unavailable storage or a malformed value
    }
    // `initial` only matters when the key changes, and callers often pass a new object each render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
