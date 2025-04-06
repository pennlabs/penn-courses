import React, { FunctionComponent, useEffect, useState } from "react";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { addBreakItem, fetchCourseDetails, createBreakItemBackend } from "../../actions";
import { Section as SectionType, Break as BreakType, Color } from "../../types";
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
  days: string[];
  timeRange: [number, number];
  manageBreaks?: {
    add: (days: string[], timeRange: [number, number]) => void;
  };
  mobileView: boolean;
}


const Button = styled.button`
    color: gray;
    padding: 5px;
    margin: 20px 10px;
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
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [selectedTimes, setSelectedTimes] = useState<[number, number]>([10.5, 22]);

  useEffect(() => {
    console.log("Selected Days:", selectedDays);
    console.log("Selected Times:", selectedTimes);
  }
    , [selectedDays, selectedTimes]);

  return (
    <Box length={1} id="breaks">
      <DayTimeSelector minRange={10.5} maxRange={22} step={1 / 60} selectedDays={selectedDays} setSelectedDays={setSelectedDays} selectedTimes={selectedTimes} setSelectedTimes={setSelectedTimes} />
      <Button onClick={() => manageBreaks?.add(selectedDays, selectedTimes)}>Add Break</Button>
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
    add: (days: string[], timeRange: [number, number]) => {
      console.log("Adding break with days:", days, "and time range:", timeRange);
      dispatch(createBreakItemBackend(days, timeRange));
    },
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(Solver);
