import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react";
import styled from "styled-components";
import { Icon } from "../bulma_derived_components";
import { DAYS_TO_DAYSTRINGS } from "../../constants/constants";
import { Day, Weekdays } from "../../types";

const RadioContainer = styled.div`
    display: flex;
    justify-content: space-between;
    padding: 9px 8px 5px 8px;
    width: 100%;
`;

const Radio = styled.div<{ $isSelected: boolean }>`
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
    width: 25px;
    height: 25px;
    cursor: pointer;
    font-weight: 500;
    font-size: 12px;
    background: ${({ $isSelected }: { $isSelected: boolean }) =>
        $isSelected ? "#868ED8 !important" : "#F4F4F4 !important"};
    color: ${({ $isSelected }: { $isSelected: boolean }) =>
        $isSelected && "white !important"};
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
        <RadioContainer>
            {Object.keys(DAYS_TO_DAYSTRINGS).map((day) => (
                <Radio
                    key={day}
                    $isSelected={selectedDay === day}
                    onClick={() => {
                        setSelectedDay(day as Day);
                        setIsActive(false);
                    }}
                >
                    <span>{day}</span>
                </Radio>
            ))}
        </RadioContainer>
    );
}
