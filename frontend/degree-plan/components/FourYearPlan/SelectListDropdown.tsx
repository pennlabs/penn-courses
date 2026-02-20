import React, { useState, useEffect, useRef } from "react";
import styled from "@emotion/styled";
import { GrayIcon } from "../common/bulma_derived_components";
import { DBObject, DegreePlan } from "../../types";
import { DarkBlueBackgroundSkeleton } from "./PanelCommon";

const ButtonContainer = styled.div<{ $isActive: boolean; }>`
    line-height: 1.5;
    position: relative;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 0.75rem;
    transition: background 0.1s ease;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    background: ${(props) => (props.$isActive ? "#F5F6F8" : "#FFF")};
    align-items: center;

    &:hover {
        background: #ebedf1;
    }

    * {
        color: #333333;
    }

    .option-icon i {
        pointer-events: auto;
        color: #b2b2b2;
    }

    .option-icon i:hover {
        color: #7E7E7E; !important;
    }

    .option-icon i.primary {
        color: "#b2b2b2";
    }

    .option-icon i.primary:hover {
        color: "#7E7E7E"; !important;
    }

    .initial-icon {
        color: white; !important;
        font-size: 1vw;
    }
`;

const ButtonLabelContainer = styled.div<{ width: number }>`
    display: flex;
    flex-grow: 1;
    font-weight: 400;
    justify-content: start;
    max-width: ${(props) => props.width}%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
`;

const DropdownRemoveButton = ({ remove }: { remove: () => void }) => (
    <GrayIcon
        onClick={(e) => {
            remove();
            e.stopPropagation();
        }}
        role="button"
        className="option-icon"
    >
        <i className="fa fa-trash" aria-hidden="true" />
    </GrayIcon>
);

const DropdownCopyButton = ({ copy }: { copy: () => void }) => (
    <GrayIcon
        onClick={(e) => {
            copy();
            e.stopPropagation();
        }}
        role="button"
        className="option-icon"
    >
        <i className="far fa-copy" aria-hidden="true" />
    </GrayIcon>
);

const DropdownRenameButton = ({ rename }: { rename: () => void }) => (
    <GrayIcon
        onClick={(e) => {
            rename();
            e.stopPropagation();
        }}
        role="button"
        className="option-icon"
    >
        <i className="far fa-edit" aria-hidden="true" />
    </GrayIcon>
)

const ScheduleOptionsContainer = styled.div`
    display: flex;
    flex-grow: 0.5;
    gap: .25rem;
    justify-content: flex-end;
    width: 25%;
`;

interface DropdownButton {
    isActive: boolean;
    text: string;
    onClick: () => void;
    makeActive: () => void;
    mutators: {
        copy?: () => void;
        remove?: (() => void);
        rename?: (() => void);
    };
}

const DropdownButton = ({
    isActive,
    text,
    onClick,
    makeActive,
    mutators: { copy, remove, rename },
}: DropdownButton) => (
    <ButtonContainer
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
        <ButtonLabelContainer width={50}>{text}</ButtonLabelContainer>
        <ScheduleOptionsContainer>
            {rename && <DropdownRenameButton rename={rename}></DropdownRenameButton>}
            {copy && <DropdownCopyButton copy={copy}></DropdownCopyButton>}
            {remove && <DropdownRemoveButton remove={remove}></DropdownRemoveButton>}
        </ScheduleOptionsContainer>
    </ButtonContainer>
);

const ScheduleDropdownContainer = styled.div<{$isActive: boolean}>`
    border-radius: 0.5rem;
    border: 0;
    outline: none;
    display: inline-flex;
    position: relative;
    vertical-align: top;
    width: 100%;

    * {
        border: 0;
        outline: none;
    }

    i.fa.fa-chevron-down::before {
        content: ${({ $isActive }: { $isActive: boolean }) =>
        $isActive ? '"\f077"' : ""} !important;
    }
`;

const DropdownTrigger = styled.div<{$isActive: boolean}>`
    margin: 0.35rem 0rem 0rem;
    height: 1.5rem;
    width: 1.5rem;
    text-align: center;
    outline: none !important;
    border: none !important;
    background: transparent;

    div {
        background: ${({ $isActive }: { $isActive: boolean }) =>
        $isActive ? "rgba(162, 180, 237, 0.38) !important" : "none"};
    }

    div:hover {
        background: rgba(175, 194, 255, 0.27);
    }
`;

const DropdownMenu = styled.div<{$isActive: boolean}>`
    margin-top: 0.1rem !important;
    display: ${({ $isActive }: { $isActive: boolean }) =>
        $isActive ? "block" : "none"};
    left: 0;
    min-width: 15rem;
    padding-top: 4px;
    position: absolute;
    top: 100%;
    z-index: 1000;
    font-size: 1rem;
`;

const DropdownContent = styled.div`
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
    padding: 0;
`;

const AddNew = styled.button`
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    border-radius: 0 !important;
    cursor: pointer;
    padding: 0.5rem 0.5rem 0.5rem 1rem;
    transition: background 0.1s ease;
    background: #fff;
    width: 100%;

    &:hover {
        background: #ebedf1;
    }

    span,
    span i {
        float: left;
        text-align: left;
        color: #669afb !important;
    }
`;

const ScheduleDropdownHeader = styled.div`
    display: flex;
    align-items: center;
    position: relative;
    width: 100%;
`

const SelectedName = styled.span`
    font-weight: 700;
    min-width: 5rem;
    font-size: 1.25rem;
`

interface SelectListDropdownProps<T extends DBObject,> {
    itemType: string; // e.g., Degree Plan or Degree
    active?: T;
    allItems: T[];
    selectItem: (id: T["id"]) => void;
    getItemName: (item: T) => string;
    mutators: {
        copy?: (item: T) => void;
        remove?: (item: T) => void;
        rename?: (item: T) => void;
        create: () => void;
    };
    isLoading: boolean;
}

const SelectListDropdown = <T extends DBObject,>({
    itemType,
    active,
    allItems,
    selectItem,
    getItemName,
    mutators: {
        copy,
        remove,
        rename,
        create,
    },
    isLoading,
}: SelectListDropdownProps<T>) => {
    const [isActive, setIsActive] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const listener = (event: Event) => {
            if (
                ref.current &&
                !ref.current.contains(event.target as HTMLElement)
            ) {
                setIsActive(false);
            }
        };
        document.addEventListener("click", listener);
        return () => {
            document.removeEventListener("click", listener);
        };
    });

    return (
        <ScheduleDropdownContainer ref={ref} $isActive={isActive}>
            <ScheduleDropdownHeader>
                <SelectedName>{active ? getItemName(active) : <DarkBlueBackgroundSkeleton />}</SelectedName>
                <DropdownTrigger
                    $isActive={isActive}
                    onClick={() => {
                        setIsActive(!isActive);
                    }}
                    role="button"
                >
                    <div aria-haspopup={true} aria-controls="dropdown-menu">
                        <GrayIcon>
                            <i className={`fa ${isActive ? 'fa-chevron-up' : 'fa-chevron-down'}`} aria-hidden="true" />
                        </GrayIcon>
                    </div>
                </DropdownTrigger>
            </ScheduleDropdownHeader>
            <DropdownMenu $isActive={isActive} role="menu">
                <DropdownContent>
                    {allItems &&
                        Object.entries(allItems)
                            .map(([idx, data]) => {
                                return (
                                    <DropdownButton
                                        key={String(data.id)}
                                        isActive={data.id === active?.id}
                                        makeActive={() => {
                                            setIsActive(false);
                                        }}
                                        onClick={() => selectItem(data.id)}
                                        text={getItemName(data)}
                                        mutators={{
                                            copy: copy && (() => copy(data)),
                                            remove: remove && (() => remove(data)),
                                            rename: rename && (() => rename(data))
                                        }}
                                    />
                                );
                            })}
                    <AddNew onClick={create} role="button" disabled={isLoading}>
                        <GrayIcon>
                            <i className="fa fa-plus" aria-hidden="true" />
                        </GrayIcon>
                        <span> Add new {itemType} </span>
                    </AddNew>
                </DropdownContent>
            </DropdownMenu>
        </ScheduleDropdownContainer>
    );
};

export default SelectListDropdown;