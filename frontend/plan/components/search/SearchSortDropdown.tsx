import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { changeSortType } from "../../actions";
import { Icon } from "../bulma_derived_components";

interface DropDownButtonProps {
    isActive: boolean;
    text: string;
    onClick: () => void;
    makeActive: () => void;
}

const DropdownButtonContainer = styled.div<{ $isActive: boolean }>`
    line-height: 1.5;
    position: relative;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 1rem;
    transition: background 0.1s ease;
    display: flex;
    flex-direction: row;
    justify-content: space-between;

    background: ${(props) => (props.$isActive ? "#F5F6F8" : "#FFF")};

    &:hover {
        background: ${(props) => (props.$isActive ? "#EBEDF1" : "#F5F6F8")};
    }

    &,
    * {
        font-size: 0.75rem;
        color: #333333;
    }
`;

const DropdownButton = ({
    isActive,
    text,
    onClick,
    makeActive,
}: DropDownButtonProps) => (
    <DropdownButtonContainer
        role="button"
        onClick={() => {
            if (onClick) {
                onClick();
            }
            if (makeActive) {
                makeActive();
            }
        }}
        $isActive={isActive}
    >
        {text}
    </DropdownButtonContainer>
);

type SortByType = "Name" | "Quality" | "Difficulty" | "Good & Easy"; // | "Suggested"
const contents: SortByType[] = ["Name", "Quality", "Difficulty", "Good & Easy"]; // TODO: re-add "Suggested"

const DropdownContainer = styled.div`
    border-radius: 0.5rem;
    border: 0;
    outline: none;
    display: inline-flex;
    position: relative;
    vertical-align: top;

    * {
        border: 0;
        outline: none;
    }
`;

const DropdownTrigger = styled.div<{ $isActive: boolean }>`
    margin-left: 0.75rem;
    height: 1.5rem;
    width: 1.5rem;
    text-align: center;
    outline: none !important;
    border: none !important;
    background: transparent;

    div {
        background: ${(props) =>
            props.$isActive ? "rgba(162, 180, 237, 0.38) !important" : "none"};
    }

    div:hover {
        background: rgba(175, 194, 255, 0.27);
    }
`;

const DropdownMenu = styled.div<{ $isActive: boolean }>`
    margin-top: 0.1rem !important;
    display: ${(props) => (props.$isActive ? "block" : "none")};
    left: 0;
    min-width: 12rem;
    padding-top: 4px;
    position: absolute;
    top: 100%;
    z-index: 20;
`;

const DropdownContent = styled.div`
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
    padding: 0;
    width: 6rem;
`;

const SearchSortDropdown = (obj: { updateSort: (s: SortByType) => void }) => {
    const [isActive, setIsActive] = useState(false);
    const [activeItem, setActiveItem] = useState(0);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const listener = (event: MouseEvent) => {
            // Cast is unavoidable https://github.com/Microsoft/TypeScript/issues/15394#issuecomment-297495746
            if (ref.current && !ref.current.contains(event.target as Node)) {
                setIsActive(false);
            }
        };
        document.addEventListener("click", listener);
        return () => {
            document.removeEventListener("click", listener);
        };
    });
    return (
        <DropdownContainer ref={ref}>
            <span className="selected_name">Sort by</span>
            <DropdownTrigger
                $isActive={isActive}
                onClick={() => setIsActive(!isActive)}
                role="button"
            >
                <div aria-haspopup={true} aria-controls="dropdown-menu">
                    <Icon>
                        <i className="fa fa-chevron-down" aria-hidden="true" />
                    </Icon>
                </div>
            </DropdownTrigger>
            <DropdownMenu $isActive={isActive} role="menu">
                <DropdownContent>
                    {contents.map((sortType, index) => (
                        <DropdownButton
                            key={index}
                            isActive={activeItem === index}
                            makeActive={() => {
                                setActiveItem(index);
                                setIsActive(false);
                            }}
                            onClick={() => obj.updateSort(sortType)}
                            text={sortType}
                        />
                    ))}
                </DropdownContent>
            </DropdownMenu>
        </DropdownContainer>
    );
};

const mapStateToProps = () => ({});
// @ts-ignore
const mapDispatchToProps = (dispatch) => ({
    // @ts-ignore
    updateSort: (sortMode) => dispatch(changeSortType(sortMode)),
});

// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(SearchSortDropdown);
