import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";
import { DAYS_TO_DAYSTRINGS } from "../../constants/constants";
import { Day } from "../../types";

const DropdownContainer = styled.div`
    margin-top: 5px;
    border-radius: 0.5rem;
    border: 0;
    outline: none;
    display: inline-flex;
    vertical-align: top;
    width: 100%;
    position: relative;
    * {
        border: 0;
        outline: none;
    }
`;

const DropdownTriggerContainer = styled.div<{ $isActive: boolean }>`
    padding-left: 0.5rem;
    display: flex;

    align-items: center;
    background: ${({ $isActive }: { $isActive: boolean }) =>
        $isActive ? "rgba(162, 180, 237, 0.38) !important" : "none"};

    :hover {
        background: rgba(175, 194, 255, 0.27);
    }
`;

const DropdownTrigger = styled.div`
    margin-left: 1rem;
    height: 1.5rem;

    text-align: center;
    outline: none !important;
    border: none !important;
    background: transparent;
`;

const DropdownText = styled.div`
    font-size: 1vw;
    font-weight: 600;
`;

const DropdownMenu = styled.div<{ $isActive: boolean }>`
    margin-top: 0.1rem !important;
    display: ${({ $isActive }) => ($isActive ? "block" : "none")};
    left: 0;
    min-width: 9rem;
    padding-top: 4px;
    position: absolute;
    top: 100%;
    z-index: 2000 !important;
`;

const DropdownContent = styled.div`
    background-color: #fff;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
    padding: 0;
`;

const DropdownButton = styled.div`
    padding-left: 6px;
    &:hover {
        background: #f5f6f8;
    }
`;

interface MapDropdownProps {
    selectedDay: Day;
    setSelectedDay: Dispatch<SetStateAction<Day>>;
}
export default function MapDropdown({
    selectedDay,
    setSelectedDay,
}: MapDropdownProps) {
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
        <DropdownContainer ref={ref}>
            <DropdownTriggerContainer
                $isActive={isActive}
                onClick={() => {
                    setIsActive(!isActive);
                }}
                role="button"
            >
                <DropdownText>{DAYS_TO_DAYSTRINGS[selectedDay]}</DropdownText>
                <DropdownTrigger>
                    <div aria-haspopup={true} aria-controls="dropdown-menu">
                        <Icon>
                            <i
                                className={`fa fa-chevron-${
                                    isActive ? "up" : "down"
                                }`}
                                aria-hidden="true"
                            />
                        </Icon>
                    </div>
                </DropdownTrigger>
            </DropdownTriggerContainer>
            <DropdownMenu $isActive={isActive} role="menu">
                <DropdownContent>
                    {Object.entries(DAYS_TO_DAYSTRINGS).map(
                        ([day, dayString]) => (
                            <DropdownButton
                                key={day}
                                onClick={() => {
                                    setSelectedDay(day as Day);
                                    setIsActive(false);
                                }}
                            >
                                {dayString}
                            </DropdownButton>
                        )
                    )}
                </DropdownContent>
            </DropdownMenu>
        </DropdownContainer>
    );
}
