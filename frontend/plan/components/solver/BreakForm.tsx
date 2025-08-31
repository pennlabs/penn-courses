import React, { useEffect, useState } from "react";
import styled from "styled-components";
import Slider from "rc-slider";

const DayTimeFilterContainer = styled.div`
    padding-top: 0.2rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    display: flex;
    flex-direction: column;
`;

const FilterRow = styled.div`
    padding: 0.25rem 0.5rem;
    flex-wrap: wrap;
    cursor: pointer;
    display: flex;
    align-items: center;
    margin-left: 8px;
`;

const FormLabel = styled.p`
    margin-bottom: 0.5rem;
    color: #363636;
    font-weight: 700;
`;

const FilterContainer = styled.div`
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 0.5rem;
`;

const Row = styled.div`
    padding: 0.75rem;
`;

const RangeFilterContainer = styled.div`
    justify-content: center;
    flex-wrap: wrap;
    width: 100%;
    padding: 0.2rem 0.8rem;
`;

interface CheckboxProps {
    checked: boolean;
}

const CheckboxInput = ({ checked }: CheckboxProps) => {
    const checkStyle = {
        width: "1rem",
        height: "1rem",
        border: "none",
        color: "#878ED8",
    };
    return (
        <div
            aria-checked="false"
            role="checkbox"
            style={{
                flexGrow: 0,
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                display: "flex",
                fontSize: "18px",
            }}
        >
            <i
                className={`${
                    checked ? "fas fa-check-square" : "far fa-square"
                }`}
                style={checkStyle}
            />
        </div>
    );
};

const StyledRangeWrapper = styled.div`
    display: block;
    padding: 0 0.75rem;

    & .rc-slider-handle {
        border-color: #7876f3 !important;
    }

    & .rc-slider-handle,
    & .rc-slider-track {
        background-color: #7876f3 !important;
    }
`;

const NameInput = styled.input`
    width: 100%;
    padding: 0.3rem;
    margin: 0.5rem 0;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #f1f1f1;
    outline: none;
`;

const SliderInputWrapper = styled.div`
    position: relative;
    width: 100%;
    height: 48px;
`;

const EndpointInput = styled.input`
    color: #4a4a4a;
    position: absolute;
    top: 65%;
    width: 70px;
    text-align: center;
    transform: translateY(-50%);
    padding: 0.2rem 0;
    border: none;
    background: #fff;
    font-size: 0.8em;
    &::-webkit-calendar-picker-indicator {
        display: none;
        -webkit-appearance: none;
    }
`;

const LeftInput = styled(EndpointInput)`
    left: -30px;
`;

const RightInput = styled(EndpointInput)`
    right: -30px;
`;

interface DayTimeSelectorProps {
    minRange: number;
    maxRange: number;
    step: number;
    selectedDays: string[];
    setSelectedDays: (days: string[]) => void;
    selectedTimes: [number, number];
    setSelectedTimes: (times: [number, number]) => void;
    name: string;
    setName: (name: string) => void;
}

export function BreakForm({
    minRange,
    maxRange,
    selectedDays,
    setSelectedDays,
    selectedTimes,
    setSelectedTimes,
    name,
    setName,
}: DayTimeSelectorProps) {
    const daysOfWeek = ["M", "T", "W", "R", "F", "S", "U"];

    const [startInput, setStartInput] = useState(
        floatToTimeString(selectedTimes[0])
    );
    const [endInput, setEndInput] = useState(
        floatToTimeString(selectedTimes[1])
    );

    useEffect(() => {
        setStartInput(floatToTimeString(selectedTimes[0]));
    }, [selectedTimes[0]]);
    useEffect(() => {
        setEndInput(floatToTimeString(selectedTimes[1]));
    }, [selectedTimes[1]]);

    const handleDayToggle = (day: string) => {
        const updatedDays = selectedDays.includes(day)
            ? selectedDays.filter((d) => d !== day)
            : [...selectedDays, day];
        setSelectedDays(updatedDays);
    };

    const handleTimeChange = (values: number | number[]) => {
        const newTimes = values as [number, number];
        setSelectedTimes(newTimes);
    };

    const handleStartInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setStartInput(e.target.value);
    };
    const handleEndInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setEndInput(e.target.value);
    };

    const handleStartInputBlur = () => {
        const val = timeStringToFloat(startInput);
        if (!isNaN(val) && val >= minRange && val <= selectedTimes[1]) {
            setSelectedTimes([val, selectedTimes[1]]);
        } else {
            setStartInput(floatToTimeString(selectedTimes[0])); // revert to valid value
        }
    };
    const handleEndInputBlur = () => {
        const val = timeStringToFloat(endInput);
        if (!isNaN(val) && val <= maxRange && val >= selectedTimes[0]) {
            setSelectedTimes([selectedTimes[0], val]);
        } else {
            setEndInput(floatToTimeString(selectedTimes[1])); // revert to valid value
        }
    };

    function timeStringToFloat(str: string): number {
        const [h, m] = str.split(":").map(Number);
        if (isNaN(h) || isNaN(m)) return NaN;
        return h + m / 60;
    }
    function floatToTimeString(t: number): string {
        const hour = Math.floor(t);
        const min = Math.round((t % 1) * 60);
        return `${hour.toString().padStart(2, "0")}:${min
            .toString()
            .padStart(2, "0")}`;
    }

    return (
        <DayTimeFilterContainer>
            <Row>
                <FormLabel>Name</FormLabel>
                <NameInput
                    type="text"
                    placeholder="Break Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
            </Row>

            <Row>
                <FormLabel>Day</FormLabel>
                <FilterContainer>
                    {daysOfWeek.map((day) => (
                        <FilterRow
                            key={"day-" + day}
                            tabIndex={0}
                            role="checkbox"
                            aria-checked={selectedDays.includes(day)}
                            onClick={() => handleDayToggle(day)}
                            onKeyDown={(e) => {
                                if (e.key === " " || e.key === "Enter") {
                                    handleDayToggle(day);
                                    e.preventDefault();
                                }
                            }}
                        >
                            <CheckboxInput
                                checked={selectedDays.includes(day)}
                            />
                            <span
                                style={{
                                    color: "#4a4a4a",
                                    marginLeft: 8,
                                    fontWeight: 500,
                                    fontSize: "0.8em",
                                }}
                            >
                                {day}
                            </span>
                        </FilterRow>
                    ))}
                </FilterContainer>
            </Row>

            <Row>
                <FormLabel>Time</FormLabel>
                <RangeFilterContainer>
                    <StyledRangeWrapper>
                        <SliderInputWrapper>
                            <LeftInput
                                type="time"
                                step={300}
                                value={startInput}
                                min={floatToTimeString(minRange)}
                                max={floatToTimeString(selectedTimes[1])}
                                onChange={handleStartInputChange}
                                onBlur={handleStartInputBlur}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        handleStartInputBlur();
                                        (e.target as HTMLInputElement).blur();
                                    }
                                }}
                            />
                            <Slider
                                range
                                min={minRange}
                                max={maxRange}
                                value={selectedTimes}
                                marks={{}}
                                step={5 / 60}
                                vertical={false}
                                allowCross={false}
                                onChange={handleTimeChange}
                            />
                            <RightInput
                                type="time"
                                step={300}
                                value={endInput}
                                min={floatToTimeString(selectedTimes[0])}
                                max={floatToTimeString(maxRange)}
                                onChange={handleEndInputChange}
                                onBlur={handleEndInputBlur}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        handleStartInputBlur();
                                        (e.target as HTMLInputElement).blur();
                                    }
                                }}
                            />
                        </SliderInputWrapper>
                    </StyledRangeWrapper>
                </RangeFilterContainer>
            </Row>
        </DayTimeFilterContainer>
    );
}
