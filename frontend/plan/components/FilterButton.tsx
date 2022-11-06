/* A button that toggles on click and allows search to filter class that only fits schedule */

import React, { ReactElement, useState } from "react";
import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { 
    DropdownContainer, 
    DropdownTrigger,
    DropdownFilterButton,
    DeleteButtonContainer,
    DeleteButton } from "./DropdownButton";

import { FilterData, FilterType } from "../types";

interface FilterButtonProps<F, K extends keyof F> {
    title: string;
    children: never[];
    filterData: FilterType;
    defaultFilter: FilterType;
    clearFilter: () => void;
    startSearch: (searchObj: F) => void;
    activeSchedule: number;
    buttonProperty: K;
    updateButtonFilter: (value: number) => void
}

export function FilterButton<
    F extends { [P in K]: [number, number] },
    K extends keyof F>({
    title,
    filterData,
    defaultFilter,
    clearFilter,
    startSearch, 
    activeSchedule,
    buttonProperty,
    updateButtonFilter
}: FilterButtonProps<F, K>) {
    const [isActive, setIsActive] = useState(false);

    const toggleButton = () => {
        console.log(activeSchedule)
        if (isActive) {
            setIsActive(false);
            clearFilter();
        } else {
            setIsActive(true);
            updateButtonFilter(activeSchedule);
            startSearch({
                // @ts-ignore
                ...filterData,
                [buttonProperty]: activeSchedule,
            });
        }
    };
    const ref = useOnClickOutside(toggleButton, true);

    return (
        <DropdownContainer ref={ref as React.RefObject<HTMLDivElement>}>
            <DropdownTrigger className="dropdown-trigger">
                <DropdownFilterButton
                    defaultData={
                        JSON.stringify(filterData) ===
                        JSON.stringify(defaultFilter)
                    }
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
