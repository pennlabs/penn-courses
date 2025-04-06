import React, { FunctionComponent, use, useEffect, useState } from "react";
import { connect, useDispatch } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { addBreakItem, updateScheduleOnBackend } from "../../actions";
import { DayTimeSelector } from "./DayTimeSelector";

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

interface SolverProps {
    name: string;
    days: string[];
    timeRange: [number, number];
    manageBreaks?: {
        add: (name:string, days: string[], timeRange: [number, number]) => void;
    };
    mobileView: boolean;
}


const Button = styled.button`
    color: gray;
    padding: 0.5rem;
    margin: 0.5rem 1.25rem;
    border: 1px lightgray solid;
    border-radius: 5px;
    background: none;
    &:hover {
        cursor: pointer;
        color: #669afb;
    }
`;

const Solver: React.FC<SolverProps> = ({
    manageBreaks,
    mobileView,
}) => {
    const [name, setName] = useState("My Break");
    const [selectedDays, setSelectedDays] = useState<string[]>([]);
    const [selectedTimes, setSelectedTimes] = useState<[number, number]>([10.5, 22]);

    return(
        <Box length={1} id="breaks">
            <DayTimeSelector minRange={10.5} maxRange={22} step={1 / 60} selectedDays={selectedDays} setSelectedDays={setSelectedDays} selectedTimes={selectedTimes} setSelectedTimes={setSelectedTimes}
            name={name} setName={setName}/>
            <Button onClick={() => {
                manageBreaks?.add(name, selectedDays, selectedTimes);
            }}>Add Break</Button>
        </Box>
    );
};

const mapStateToProps = ({
    // days: { selectedDays },
    // times: { selectedTimes },
}: any) => ({
    // days: selectedDays,
    // times: selectedTimes,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    manageBreaks: {
        add: (name:string, days: string[], timeRange: [number, number]) => {
            dispatch(addBreakItem(name, days, timeRange));
        },
    },
});

export default connect(mapStateToProps, mapDispatchToProps)(Solver);
