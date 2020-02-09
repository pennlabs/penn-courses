import React, { useState } from "react";
import PropTypes from "prop-types";
import { useOnClickOutside } from "./useOnClickOutside";

export function DropdownButton({
    render
}) {
    const [isActive, setIsActive] = useState(false);

    const toggleButton = () => {
        if (isActive) {
            setIsActive(false);
        } else {
            setIsActive(true);
        }
    };

    const ref = useOnClickOutside(toggleButton, !isActive);

    return (
        <div
            className={`dropdown ${isActive ? "is-active" : ""}`}
            ref={ref}
        >
            {render(toggleButton)}
        </div>
    );
}
