import React, { useState } from "react";
import PropTypes from "prop-types";
import { useOnClickOutside } from "./useOnClickOutside";

export function DropdownButton({ title, children, filterData, defaultFilter }) {
    const [isActive, setIsActive] = useState(false);

    const toggleButton = () => {
        if (isActive) {
            setIsActive(false);
        } else {
            setIsActive(true);
        }
    };
    // console.log(filterData);
    // console.log(defaultFilter);
    const ref = useOnClickOutside(toggleButton, !isActive);

    return (
        <div
            className={`dropdown ${isActive ? "is-active" : ""}`}
            ref={ref}
        >
            <div className="dropdown-trigger">
                <button
                    className="button is-rounded"
                    aria-haspopup="true"
                    aria-controls="dropdown-menu"
                    onClick={toggleButton}
                    type="button"
                >
                    <span>
                        {title}
                    </span>
                    {JSON.stringify(filterData) !== JSON.stringify(defaultFilter)
                    && (
                        <span>
                            <i
                                className="delete is-small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                }}
                                role="button"
                            />
                        </span>
                    )}
                </button>
            </div> 
            <div className="dropdown-menu" id="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    {/* This injects the setIsActive method to allow children */}
                    {/* to change state of dropdown  */}
                    {React.Children.map(children, c => (
                        React.cloneElement(c, {
                            setIsActive,
                        })
                    ))}
                </div>
            </div>
        </div>
    );
}

DropdownButton.propTypes = {
    title: PropTypes.string,
    children: PropTypes.arrayOf(PropTypes.object),
};
