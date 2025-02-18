import { useEffect, useState } from "react";

export const useDebouncedState = <T>(
    initialValue: T,
    delay = 100
): [T, T, (value: T) => void] => {
    const [value, setValue] = useState(initialValue);
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);
    return [value, debouncedValue, setValue];
};
