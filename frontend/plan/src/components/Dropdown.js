import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

const DropdownButton = ({
    index, activeItem, modifyLabel, text,
    setLabelText, onClick, setActiveItem,
    isCategory,
}) => (
    <button
        key={index}
        onClick={() => {
            if (onClick) {
                onClick();
            }
            if (isCategory) {
                setActiveItem(index);
                if (modifyLabel) {
                    setLabelText(text);
                }
            }
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
);

DropdownButton.propTypes = {
    index: PropTypes.number.isRequired,
    activeItem: PropTypes.number.isRequired,
    modifyLabel: PropTypes.bool,
    text: PropTypes.string,
    setLabelText: PropTypes.func,
    onClick: PropTypes.func,
    setActiveItem: PropTypes.func,
    isCategory: PropTypes.bool,
};

const Dropdown = ({
    defActive, defText, contents, modifyLabel,
}) => {
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
                        .map(([index, { onClick, text, isCategory }]) => (
                            <DropdownButton
                                index={index}
                                activeItem={activeItem}
                                modifyLabel={modifyLabel}
                                setLabelText={setLabelText}
                                setActiveItem={setActiveItem}
                                isCategory={isCategory}
                                onClick={onClick}
                                text={text}
                            />
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
    modifyLabel: PropTypes.bool,
};


export default Dropdown;
