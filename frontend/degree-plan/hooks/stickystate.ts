import { useState, useEffect } from "react";

function useStickyState<T>(defaultValue: T, key: string): [T, (value: T) => void] {
    const [value, setValue] = useState<T>(() => {
        if (typeof window === "undefined") return defaultValue; // SSR
        const stickyValue = localStorage.getItem(key);
        return stickyValue !== null
        ? JSON.parse(stickyValue)
        : defaultValue;
    });
    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);
    return [value, setValue];
}

export default useStickyState;