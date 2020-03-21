import { useEffect, useRef } from "react";

/**
 * useOnClickOutside is a hook that lets a component call a function when
 * a click is detected outside of the component (e.g. dropdowns)
 *
 * @param {function} onClickOutside The function called when an outside click is detected
 * @param {boolean} disabled Whether the hook should still listen for outside click
 * @return {Object} A ref to be passed as a ref props to the component that uses useOnClickOutside
 */

export function useOnClickOutside(onClickOutside, disabled) {
    const ref = useRef();
    // eslint-disable-next-line consistent-return
    useEffect(() => {
        const checkClickOutside = (e) => {
            if (ref.current) {
                if (!ref.current.contains(e.target)) {
                    onClickOutside();
                }
            }
        };
        if (!disabled) {
            window.addEventListener("click", checkClickOutside);
            return () => {
                window.removeEventListener("click", checkClickOutside);
            };
        }
    }, [disabled, onClickOutside]);

    return ref;
}
