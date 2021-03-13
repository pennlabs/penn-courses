import { useEffect, useRef } from "react";

/**
 * useOnClickOutside is a hook that lets a component call a function when
 * a click is detected outside of the component (e.g. dropdowns)
 *
 * @param {function} onClickOutside The function called when an outside click is detected
 * @param {boolean} disabled Whether the hook should still listen for outside click
 * @param {string} ignoreClassName  The className to ignore if it is clicked
 * @return {Object} A ref to be passed as a ref props to the component that uses useOnClickOutside
 */

export function useOnClickOutside(onClickOutside, disabled, ignoreEle) {
    const ref = useRef();
    // eslint-disable-next-line consistent-return
    useEffect(() => {
        const checkClickOutside = (e) => {
            if (ref.current) {
                // if ignoreEle param is added
                if (ignoreEle) {
                    if (
                        !e.target.classList.contains(ignoreEle) &&
                        !e.target.parentElement.classList.contains(ignoreEle) &&
                        !ref.current.contains(e.target)
                    ) {
                        onClickOutside();
                    }
                } else if (!ref.current.contains(e.target)) {
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
    }, [disabled, onClickOutside, ignoreEle]);

    return ref;
}
