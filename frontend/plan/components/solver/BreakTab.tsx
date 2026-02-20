import React, { useState } from "react";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { createBreakBackend, removeBreakBackend } from "../../actions";
import { showToast } from "../../pages";
import { Break } from "../../types";
import { BreakForm } from "./BreakForm";
import BreakSection from "./BreakSection";
import { getTimeString } from "../meetUtil";

const Box = styled.section<{ length: number }>`
    height: calc(100vh - 9em - 3em);
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    background-color: white;
    color: #4a4a4a;
    overflow: ${(props) => (props.length === 0 ? "hidden" : "auto")};
    flex-direction: column;
    padding: 0;
    display: flex;
    @media (max-width: 800px) {
        min-height: calc(100vh - 8em);
        height: 100%;
        box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.1);
    }

    &::-webkit-scrollbar {
        width: 0.5em;
        height: 0.5em;
    }

    &::-webkit-scrollbar-track {
        background: white;
    }

    &::-webkit-scrollbar-thumb {
        background: #95a5a6;
        border-radius: 1px;
    }
`;

interface BreakProps {
    days?: string[];
    timeRange?: [number, number];
    manageBreaks?: {
        add: (
            name: string,
            days: string[],
            timeRange: [number, number],
            breaks: Break[]
        ) => void;
        remove: (breakItem: Break, toggle: boolean) => void;
    };
    mobileView: boolean;
    breaks: Break[];
    scheduleCheckedBreaks: Break[];
    toggleBreak: (breakItem: Break) => void;
}

const Button = styled.button`
    padding: 0.5em 1.25em;
    background: #fff;
    color: #7e7e7e;
    border: solid 0.1rem #dadada;
    border-radius: 30px;
    font-weight: 600;
    font-size: 0.8rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    transition: background 0.15s, color 0.15s, border 0.15s;
    margin-left: 1rem;
    margin-top: 0.6rem;

    &:hover {
        background: rgb(247, 247, 247);
        color: rgb(90, 90, 90);
        border-bottom-color: rgb(218, 218, 218);
        outline: none;
    }

    &:active {
        outline: none;
        box-shadow: 0 0 0 0.125em rgb(50 115 220 / 25%);
        color: #7876f3;
        border: solid 0.1rem #7876f3;
        background-color: #fff;
    }
`;

const BreakAddSection = styled.div`
    border-bottom: 1px solid #e5e8eb;
    padding-bottom: 1rem;
`;

const BreakTab: React.FC<BreakProps> = ({
    breaks,
    scheduleCheckedBreaks,
    toggleBreak,
    manageBreaks,
}) => {
    const [selectedDays, setSelectedDays] = useState<string[]>([]);
    const [selectedTimes, setSelectedTimes] = useState<[number, number]>([
        10.5,
        22,
    ]);
    const [name, setName] = useState<string>("");

    return (
        <>
            <Box length={breaks.length + 1} id="breaks">
                <BreakAddSection>
                    <BreakForm
                        minRange={10.5}
                        maxRange={22}
                        step={1 / 60}
                        selectedDays={selectedDays}
                        setSelectedDays={setSelectedDays}
                        selectedTimes={selectedTimes}
                        setSelectedTimes={setSelectedTimes}
                        name={name}
       
                        setName={setName}
                    />
                    <Button
                        onClick={() =>
                            manageBreaks?.add(name, selectedDays, selectedTimes, breaks)
                        }
                    >
                        Add Break
                    </Button>
                </BreakAddSection>
                {breaks.map((breakItem, i) => {
                    const isChecked = scheduleCheckedBreaks.some(
                        br => br.id === breakItem.id
                    );
                    return (
                        <BreakSection
                            key={i}
                            name={breakItem.name}
                            checked={isChecked}
                            time={getTimeString(breakItem.meetings ?? [])}
                            toggleCheck={() => toggleBreak(breakItem)}
                            remove={(e) => {
                                e.stopPropagation();
                                manageBreaks?.remove(breakItem, isChecked);
                            }}
                        />
                    );
                })}
            </Box>
        </>
    );
};

const validateBreakInput = (name: string, days: string[], timeRange: [number, number], existingBreaks: Break[]) => {
    if (!name || name.trim() === "") {
        return "Break name cannot be empty.";
    }
    if (existingBreaks.some(b => b.name === name)) {
        return "Break name must be unique.";
    }
    if (days.length === 0) {
        return "Please select at least one day for the break.";
    }
    if (timeRange[0] >= timeRange[1]) {
        return "Start time must be before end time.";
    }
    if (existingBreaks.length >= 10) {
        return "You can only have up to 10 breaks.";
    }
    return null;
}

const mapStateToProps = ({
    schedule: { scheduleSelected, schedules },
    breaks: {breaks}
}: any) => ({
    breaks: breaks,
    scheduleCheckedBreaks: schedules[scheduleSelected]?.breaks || [], 
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    manageBreaks: {
        add: (name: string, days: string[], timeRange: [number, number], breaks: Break[]) => {
          const error = validateBreakInput(name, days, timeRange, breaks);
          if (error) {
            showToast(error, true);
          }
          dispatch(createBreakBackend(name, days, timeRange));
        },
        remove: (breakItem: Break, toggle: boolean) => {
          if (toggle) {
            dispatch({ type: "TOGGLE_BREAK", breakItem });
          }
          dispatch(removeBreakBackend(breakItem.id));
        },
    },
    toggleBreak: (breakItem: Break) => {
        dispatch({ type: "TOGGLE_BREAK", breakItem });
    },
});

export default connect(mapStateToProps, mapDispatchToProps)(BreakTab);
