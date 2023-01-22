/* A button that toggles on click and allows search to filter class that only fits schedule */

import React, { useState } from "react";
import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { 
    DropdownContainer, 
    DropdownTrigger,
    DropdownFilterButton,
    DeleteButtonContainer,
    DeleteButton } from "../DropdownButton";

import { FilterData, FilterType } from "../../types";

interface ButtonFilterProps<F, K extends keyof F> {
    title: string;
    children: never[];
    filterData: F;
    defaultFilter: FilterType;
    clearFilter: () => void;
    startSearch: (searchObj: F) => void;
    value: number;
    buttonProperty: K;
    updateButtonFilter: (value: any) => void
}

export function ButtonFilter<
    F extends { [P in K]: number | boolean },
    K extends keyof F>({
    title,
    filterData,
    defaultFilter,
    clearFilter,
    startSearch, 
    value,
    buttonProperty,
    updateButtonFilter
}: ButtonFilterProps<F, K>) {
    const [isActive, setIsActive] = useState(false);

    const toggleButton = () => {
        if (isActive) {
            clearFilter();
            setIsActive(false);
        } else {
            setIsActive(true);
            if (buttonProperty === "fit_schedule") {
                updateButtonFilter(value);
                startSearch({
                    ...filterData,
                    [buttonProperty]: {[value]: null},
                });
            } else if (buttonProperty === "is_open") {
                updateButtonFilter(isActive);
                startSearch({
                    ...filterData,
                    [buttonProperty]: {[`${isActive}`]: null},
                });
            } 
            
        }
    };
    const ref = useOnClickOutside(toggleButton, true);

    return (
        <DropdownContainer ref={ref as React.RefObject<HTMLDivElement>}>
            <DropdownTrigger className="dropdown-trigger">
                <DropdownFilterButton
                    defaultData={!isActive}
                    aria-haspopup="true"
                    aria-controls="dropdown-menu"
                    onClick={toggleButton}
                    type="button"
                >
                    <div>{title}</div>
                    { isActive && (
                        <DeleteButtonContainer>
                            <DeleteButton
                                type="button"
                                className="delete is-small"
                                onClick={(e) => {
                                    clearFilter();
                                    e.stopPropagation();
                                    setIsActive(false);
                                }}
                            />
                        </DeleteButtonContainer>
                    )}
                </DropdownFilterButton>
            </DropdownTrigger>
        </DropdownContainer>
    );
}
