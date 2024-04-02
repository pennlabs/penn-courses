import React, { ReactElement, useState } from "react";
import styled from "styled-components";
import { useOnClickOutside } from "../../../shared-components/src/useOnClickOutside";
import { FilterType } from "../../types";

interface DropdownButtonProps {
    title: string;
    filterData: FilterType;
    defaultFilter: FilterType;
    clearFilter: () => void;
}

export const DropdownContainer = styled.div`
    display: inline-flex;
    position: relative;
    vertical-align: top;
`;

export const DropdownTrigger = styled.div`
    margin: 0.2em;
`;

export const DropdownFilterButton = styled.button<{ $defaultData: boolean }>`
    padding: calc(0.375em - 1px) 0.75em;
    padding-left: 1em;
    padding-right: 1em;
    background-color: #fff;
    cursor: pointer;
    justify-content: center;
    text-align: center;
    white-space: nowrap;
    position: relative;
    font-weight: bold;
    display: flex;
    align-items: center;
    height: 100%;
    border-radius: 30px !important;
    font-size: 0.75rem !important;
    line-height: 1.5;

    transition-duration: ${({ $defaultData }) =>
        $defaultData ? "" : "0.2s"};
    border: solid 0.1rem
        ${({ $defaultData }) =>
            $defaultData ? "#dadada" : "#7876f3"};
    color: ${({ $defaultData }) =>
        $defaultData ? "#7e7e7e" : "#7876f3"};
    flex-grow: 1;
    background-color: ${({ $defaultData }) =>
        $defaultData ? "#fff" : "#ebebfd"};

    &:hover {
        background-color: ${({ $defaultData }) =>
            $defaultData ? "#f7f7f7" : "#ebebfd"};
        color: ${({ $defaultData }) =>
            $defaultData ? "#5a5a5a" : "#7876f3"};
        border: ${({ $defaultData }) =>
            $defaultData ? "" : "0.1rem solid #7876f3"};
    }

    &:active {
        outline: none;
        border: solid 0.1rem #7876f3;
        background-color: #e3e6ff;
        color: ${({ $defaultData }) =>
            $defaultData ? "#7e7e7e" : "#7876f3"};
    }

    &:focus {
        outline: none;
        box-shadow: 0 0 0 0.125em rgb(50 115 220 / 25%);
        color: #7876f3;
        border: solid 0.1rem #7876f3;
        background-color: ${({ $defaultData }) =>
            $defaultData ? "#fff" : "#ebebfd"};
    }
`;

export const DeleteButtonContainer = styled.div`
    padding-left: 0.5em;
    margin-right: -0.5em;
    height: 16px;
`;

export const DeleteButton = styled.button`
    line-height: 1.5;
`;

const DropdownMenu = styled.div<{ $active: boolean }>`
    margin-top: 0.7rem;
    display: ${({ $active }) =>
        $active ? "block" : "none"};
    left: 0;
    min-width: 12rem;
    padding-top: 4px;
    position: absolute;
    top: 100%;
    z-index: 20;
`;

const DropdownContent = styled.div`
    background-color: white;
    border-radius: 4px;
    box-shadow: 0 2px 3px rgb(10 10 10 / 10%), 0 0 0 1px rgb(10 10 10 / 10%);
    padding-bottom: 0.5rem;
    padding-top: 0.5rem;
`;

export function DropdownButton({
    title,
    children,
    filterData,
    defaultFilter,
    clearFilter,
}: React.PropsWithChildren<DropdownButtonProps>) {
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
                    $defaultData={
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
            <DropdownMenu id="dropdown-menu" role="menu" $active={isActive}>
                <DropdownContent>
                    {/* This injects the setIsActive method to allow children */}
                    {/* to change state of dropdown  */}
                    {/* 
                    We need this ts-ignore because React.Children.map does
                    not allow the children to be typed as an array of ReactElements
                    in modern react (it has a broader type).
                    // @ts-ignore */}
                    {React.Children.map(children, (c: ReactElement) =>
                        React.cloneElement(c, {
                            setIsActive,
                        })
                    )}
                </DropdownContent>
            </DropdownMenu>
        </DropdownContainer>
    );
}
