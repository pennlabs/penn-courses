import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

const DropdownButton = ({ isActive, text, onClick, makeActive, copy }) => (
    <div
        onClick={e => {
            const targetClass = e.target.getAttribute("class");
            if (targetClass && (targetClass.indexOf("s-option") !== -1)) {
                // one of the icons has been clicked
                return;
            }
            if (onClick) {
                onClick();
            }
            if (makeActive) {
                makeActive();
            }
        }}
        className={`dropdown-item${isActive ? " is-active" : ""} button`}
    >
        <div className={"schedule-name-container"}>
            {text}
        </div>
        <div className={"schedule-options-container"}>
            <span className="icon is-small">
                <i className="far fa-edit" aria-hidden="true"/>
            </span>
            <div onClick={copy} className={"s-option-copy"}>
                <span className="icon is-small">
                    <i className="far fa-copy" aria-hidden="true"/>
                </span>
            </div>
            <span className="icon is-small">
                <i className="fa fa-trash" aria-hidden="true"/>
            </span>
        </div>
    </div>
);

DropdownButton.propTypes = {
    isActive: PropTypes.bool,
    text: PropTypes.string,
    onClick: PropTypes.func,
    makeActive: PropTypes.func,
    copy: PropTypes.func.isRequired,
};

const ScheduleSelectorDropdown = ({ defActive, defText, contents, copy }) => {
    const [isActive, setIsActive] = useState(false);
    const [activeItem, setActiveItem] = useState(defActive);
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
            className={`classic dropdown${isActive
                ? " is-active" : ""}`}
        >
            <span className="selected_name">{defText}</span>
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
                        <span className="icon is-small">
                            <i className="fa fa-angle-down" aria-hidden="true"/>
                        </span>
                    </span>
                </button>
            </div>
            <div className="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    {Array.from(contents.entries())
                        .map(([index, { onClick, text }]) => (
                            <DropdownButton
                                key={index}
                                isActive={activeItem === index}
                                makeActive={() => setActiveItem(index)}
                                onClick={onClick}
                                text={text}
                                copy={() => copy(text)}
                            />
                        ))}
                    <button
                        onClick={() => {
                        }}
                        type="button"
                        className="dropdown-item button light-blue"
                    >
                        + Add new schedule
                    </button>
                </div>
            </div>
        </div>
    );
};

ScheduleSelectorDropdown.propTypes = {
    defActive: PropTypes.bool,
    defText: PropTypes.string.isRequired,
    contents: PropTypes.arrayOf(PropTypes.object).isRequired,
    copy: PropTypes.func.isRequired,
};


export default ScheduleSelectorDropdown;
