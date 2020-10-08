import React, { useState, useEffect } from "react";

interface DropdownButton {
    isActive: boolean;
    text: string;
    onClick: () => void;
    makeActive: () => void;
    mutators: {
        copy: () => void;
        remove: () => void;
        rename: () => void;
    };
}

const DropdownButton = ({
    isActive,
    text,
    onClick,
    makeActive,
    mutators: { copy, remove, rename },
}: DropdownButton) => (
    <div
        role="button"
        onClick={(e) => {
            // NOTE: explicit cast to HTMLElement to resolve compile error
            // .getAttribute doesn't exist on type EventTarget
            const targetClass = (e.target as HTMLElement).getAttribute("class");
            if (targetClass && targetClass.indexOf("s-option") !== -1) {
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
        <div className="schedule-name-container">{text}</div>
        <div className="schedule-options-container">
            <div onClick={rename} className="s-option-copy" role="button">
                <span className="icon is-small">
                    <i className="far fa-edit" aria-hidden="true" />
                </span>
            </div>
            <div onClick={copy} className="s-option-copy" role="button">
                <span className="icon is-small">
                    <i className="far fa-copy" aria-hidden="true" />
                </span>
            </div>
            <div onClick={remove} className="s-option-copy" role="button">
                <span className="icon is-small">
                    <i className="fa fa-trash" aria-hidden="true" />
                </span>
            </div>
        </div>
    </div>
);

interface ScheduleSelectorDropdownProps {
    activeName: string;
    contents: {
        text: string;
        onClick: () => void;
    }[]; // FIX TYPE
    mutators: {
        copy: (scheduleName: string) => void;
        remove: (scheduleName: string) => void;
        create: () => void;
        rename: (oldName: string) => void;
    };
}

const ScheduleSelectorDropdown = ({
    activeName,
    contents,
    mutators: { copy, remove, rename, create },
}: ScheduleSelectorDropdownProps) => {
    const [isActive, setIsActive] = useState(false);
    const [ref, setRef] = useState(null);

    useEffect(() => {
        const listener = (event: Event) => {
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
            ref={(node) => setRef(node)}
            className={`classic dropdown${isActive ? " is-active" : ""}`}
        >
            <span className="selected_name">{activeName}</span>
            <div
                className="classic-dropdown-trigger"
                onClick={() => setIsActive(!isActive)}
                role="button"
            >
                <div aria-haspopup={true} aria-controls="dropdown-menu">
                    <span className="icon is-small">
                        <i className="fa fa-chevron-down" aria-hidden="true" />
                    </span>
                </div>
            </div>
            <div className="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    {Array.from(contents.entries()).map(
                        ([index, { onClick, text: scheduleName }]) => (
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
                        )
                    )}
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

export default ScheduleSelectorDropdown;
