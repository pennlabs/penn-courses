import React, { ReactElement, useState } from "react";
import styled from "styled-components";
import { useOnClickOutside } from "pcx-shared-components/src/useOnClickOutside";
import { 
    DropdownContainer, 
    DropdownTrigger,
    DropdownFilterButton,
    DeleteButtonContainer,
    DeleteButton } from "./DropdownButton";

import { FilterType } from "../types";

interface FilterButtonProps {
    title: string;
    children: never[];
    filterData: FilterType;
    defaultFilter: FilterType;
    clearFilter: () => void;
}

export function FilterButton({
    title,
    filterData,
    defaultFilter,
    clearFilter,
}: FilterButtonProps) {
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
                    {JSON.stringify(filterData) !==
                        JSON.stringify(defaultFilter) && (
                        <DeleteButtonContainer>
                            <DeleteButton
                                type="button"
                                className="delete is-small"
                                onClick={(e) => {
                                    clearFilter();
                                    e.stopPropagation();
                                }}
                            />
                        </DeleteButtonContainer>
                    )}
                </DropdownFilterButton>
            </DropdownTrigger>
        </DropdownContainer>
    );
}