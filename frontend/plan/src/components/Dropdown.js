import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

const Dropdown = ({ defActive, defText, contents }) => {
    const [isActive, setIsActive] = useState(false);
    const [activeItem, setActiveItem] = useState(defActive);
    const [labelText, setLabelText] = useState(defText);
    const [ref, setRef] = useState(null);

    useEffect(() => {
        const listener = (event) => {
            if (ref && !ref.contains(event.target)) {
                setIsActive(false);
            }
        };
        document.addEventListener("click", listener);
        return () => {
            document.removeEventListener("click", listener);
        };
    });
    return (
        <div
            ref={node => setRef(node)}
            className={`dropdown${isActive
                ? " is-active" : ""}`}
        >
            <div
                className="dropdown-trigger"
                onClick={() => setIsActive(!isActive)}
                role="button"
            >
                <button
                    className="button"
                    aria-haspopup={true}
                    aria-controls="dropdown-menu"
                    type="button"
                >
                    <span>
                        <span className="selected_name">{labelText}</span>
                        <span className="icon is-small">
                            <i className="fa fa-angle-down" aria-hidden="true" />
                        </span>
                    </span>
                </button>
            </div>
            <div className="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    {Array.from(contents.entries())
                        .map(([index, { onClick, text }]) => (
                            <button
                                key={index}
                                onClick={() => {
                                    if (onClick) {
                                        onClick();
                                    }
                                    setActiveItem(index);
                                    setLabelText(text);
                                }}
                                type="button"
                                className={`dropdown-item${activeItem === index
                                    ? " is-active" : ""} button`}
                                style={{
                                    border: "none",
                                    marginBottom: "0.2em",
                                }}
                            >
                                {text}
                            </button>
                        ))}
                </div>
            </div>
        </div>
    );
};

Dropdown.propTypes = {
    defActive: PropTypes.bool,
    defText: PropTypes.string.isRequired,
    contents: PropTypes.arrayOf(PropTypes.object).isRequired,
};


export default Dropdown;
