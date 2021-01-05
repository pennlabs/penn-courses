import React, { ReactElement, useState } from "react";
import { useOnClickOutside } from "../../shared-components/src/useOnClickOutside";

import { FilterType } from "../types";

interface DropdownButtonProps {
    title: string;
    children: ReactElement;
    filterData: FilterType;
    defaultFilter: FilterType;
    clearFilter: () => void;
}

export function DropdownButton({
    title,
    children,
    filterData,
    defaultFilter,
    clearFilter,
}: DropdownButtonProps) {
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
            ref={ref as React.RefObject<HTMLDivElement>}
        >
            <div className="dropdown-trigger">
                <button
                    className={`button is-rounded
                        ${
                            JSON.stringify(filterData) ===
                            JSON.stringify(defaultFilter)
                                ? "filterButton"
                                : "filterButtonActive"
                        }`}
                    aria-haspopup="true"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        height: "100%",
                    }}
                    aria-controls="dropdown-menu"
                    onClick={toggleButton}
                    type="button"
                >
                    <div>{title}</div>
                    {JSON.stringify(filterData) !==
                        JSON.stringify(defaultFilter) && (
                        <div
                            style={{
                                paddingLeft: "0.5em",
                                marginRight: "-0.5em",
                                height: "16px",
                            }}
                        >
                            <button
                                type="button"
                                className="delete is-small"
                                onClick={e => {
                                    clearFilter();
                                    e.stopPropagation();
                                }}
                            />
                        </div>
                    )}
                </button>
            </div>
            <div className="dropdown-menu" id="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    {/* This injects the setIsActive method to allow children */}
                    {/* to change state of dropdown  */}
                    {React.Children.map(children, (c: ReactElement) =>
                        React.cloneElement(c, {
                            setIsActive,
                        })
                    )}
                </div>
            </div>
        </div>
    );
}
