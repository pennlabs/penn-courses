import React, { useEffect, useState } from "react";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import styled from "styled-components";
import { createBreakItemBackend } from "../../actions";
import { Section as SectionType, Break as BreakType, BreakSectionItem } from "../../types";
import { DayTimeSelector } from "./DayTimeSelector";
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
  days: string[];
  timeRange: [number, number];
  manageBreaks?: {
    add: (name: string, days: string[], timeRange: [number, number]) => void;
  };
  mobileView: boolean;
  breaks: BreakSectionItem[];
  toggleBreak: (breakId: string) => void;
  removeBreak: (breakId: string) => void;
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

const BreakAddSection = styled.div`
  border-bottom: 1px solid #e5e8eb;
  padding-bottom: 1rem;
`;

const BreakTab: React.FC<BreakProps> = ({
  breaks,
  toggleBreak,
  removeBreak,
  manageBreaks,
  mobileView,
}) => {
  const [selectedDays, setSelectedDays] = useState<string[]>([]);
  const [selectedTimes, setSelectedTimes] = useState<[number, number]>([10.5, 22]);
  const [name, setName] = useState<string>("");

  return (
    <>
        <Box length={breaks.length + 1} id="breaks">
          <BreakAddSection>
            <DayTimeSelector minRange={10.5} maxRange={22} step={1 / 60} selectedDays={selectedDays} setSelectedDays={setSelectedDays} selectedTimes={selectedTimes} setSelectedTimes={setSelectedTimes} name={name} setName={setName} />
            <Button onClick={() => manageBreaks?.add(name, selectedDays, selectedTimes)}>Add Break</Button>
          </BreakAddSection>
          {
          breaks.map((breakItem, i) => (
              <BreakSection
              key={i}
              name={breakItem.break.name}
              checked={breakItem.checked}
              time={getTimeString(breakItem.break.meetings)}
              toggleCheck={() => toggleBreak(breakItem.break.name)}
              remove={(e) => {
                  e.stopPropagation();
                  removeBreak(breakItem.break.name);
              }}
              />
          ))}
        </Box>
    </>
  );
};

const mapStateToProps = ({
  schedule: { breakSections = [] },
}: any) => ({
  breaks: breakSections,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
  manageBreaks: {
    add: (name: string, days: string[], timeRange: [number, number]) => {
      dispatch(createBreakItemBackend(name, days, timeRange));
    },
  },
  toggleBreak: (breakId: string) => {
    dispatch({ type: "TOGGLE_BREAK", name: breakId });
  },
  removeBreak: (breakId: string) => {
    dispatch({ type: "REMOVE_BREAK", name: breakId });
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(BreakTab);
