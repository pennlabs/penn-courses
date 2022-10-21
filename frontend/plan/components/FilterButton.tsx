import React, { ReactElement, useState } from "react";
import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { 
    DropdownContainer, 
    DropdownTrigger,
    DropdownFilterButton,
    DeleteButtonContainer,
    DeleteButton } from "./DropdownButton";

import { FilterType } from "../types";

interface FilterButtonProps<F> {
    title: string;
    children: never[];
    filterData: FilterType;
    defaultFilter: FilterType;
    clearFilter: () => void;
    startSearch: (searchObj: F) => void;
}

export function FilterButton<F>({
    title,
    filterData,
    defaultFilter,
    clearFilter,
    startSearch
}: FilterButtonProps<F>) {
    const [isActive, setIsActive] = useState(false);

    const toggleButton = () => {
        if (isActive) {
            setIsActive(false);
        } else {
            setIsActive(true);
        }
    };
    const ref = useOnClickOutside(toggleButton, true);

    return (
        <DropdownContainer ref={ref as React.RefObject<HTMLDivElement>}>
            <DropdownTrigger className="dropdown-trigger">
                <DropdownFilterButton
                    defaultData={
                        !isActive
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