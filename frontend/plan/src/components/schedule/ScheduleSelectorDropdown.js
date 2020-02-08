import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

const DropdownButton = ({
    isActive, text, onClick, makeActive, mutators: { copy, remove, rename },
}) => (
    <div
        role="button"
        onClick={(e) => {
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
        className={`dropdown-item${isActive ? " is-active" : ""}`}
    >
        <div className="schedule-name-container">
            {text}
        </div>
        <div className="schedule-options-container">
            <div
                onClick={rename}
                className="s-option-copy"
                role="button"
            >
                <span className="icon is-small">
                    <i className="far fa-edit" aria-hidden="true" />
                </span>
            </div>
            <div
                onClick={copy}
                className="s-option-copy"
                role="button"
            >
                <span className="icon is-small">
                    <i className="far fa-copy" aria-hidden="true" />
                </span>
            </div>
            <div
                onClick={remove}
                className="s-option-copy"
                role="button"
            >
                <span className="icon is-small">
                    <i className="fa fa-trash" aria-hidden="true" />
                </span>
            </div>
        </div>
    </div>
);

DropdownButton.propTypes = {
    isActive: PropTypes.bool,
    text: PropTypes.string,
    onClick: PropTypes.func,
    makeActive: PropTypes.func,
    mutators: PropTypes.shape({
        copy: PropTypes.func.isRequired,
        remove: PropTypes.func.isRequired,
        rename: PropTypes.func.isRequired,
    }),
};

const ScheduleSelectorDropdown = ({
    activeName, contents, mutators: {
        copy, remove, rename, create,
    },
}) => {
    const [isActive, setIsActive] = useState(false);
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
            <div
                className="myDropdown"
                onClick={() => setIsActive(!isActive)}
                role="button"
            >
                <div
                    aria-haspopup={true}
                    aria-controls="dropdown-menu"
                    style={{ margin: "-0.1em" }}
                >
                    <span className="selected_name">{activeName}</span>
                    <span className="icon is-small">
                        <i className="fa fa-chevron-down" aria-hidden="true" />
                    </span>
                </div>
            </div>
            <div className="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    {Array.from(contents.entries())
                        .map(([index, { onClick, text: scheduleName }]) => (
                            <DropdownButton
                                key={index}
                                isActive={scheduleName === activeName}
                                makeActive={() => {
                                    setIsActive(false);
                                }}
                                onClick={onClick}
                                text={scheduleName}
                                mutators={{
                                    copy: () => copy(scheduleName),
                                    remove: () => remove(scheduleName),
                                    rename: () => rename(scheduleName),
                                }}
                            />
                        ))}
                    <a
                        onClick={create}
                        role="button"
                        className="dropdown-item add-schedule"
                        href="#"
                    >
                        <span className="icon is-small">
                            <i className="fa fa-plus" aria-hidden="true" />
                        </span>
                        <span> Add new schedule </span>
                    </a>
                </div>
            </div>
        </div>
    );
};

ScheduleSelectorDropdown.propTypes = {
    activeName: PropTypes.string,
    contents: PropTypes.arrayOf(PropTypes.object).isRequired,
    mutators: PropTypes.shape({
        copy: PropTypes.func.isRequired,
        remove: PropTypes.func.isRequired,
        create: PropTypes.func.isRequired,
        rename: PropTypes.func.isRequired,
    }),
};


export default ScheduleSelectorDropdown;
