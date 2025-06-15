import React, { useState } from "react";
import styled from "styled-components";
import Slider from "rc-slider";
import { Column, CheckboxInput, CheckboxLabel } from "../bulma_derived_components";

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
`;

const FilterContainer = styled.div`
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 0.5rem;
`;

const DayRow = styled.div`
    padding: 0.75rem;
`;

const NameRow = styled.div`
    padding: 0.75rem;
`;

const RangeFilterContainer = styled.div`
    justify-content: center;
    flex-wrap: wrap;
    width: 100%;
    padding: 0.2rem 0.8rem 20px;
`;

const StyledRangeWrapper = styled.div`
    display: block;
    padding: 0.75rem;

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
    padding: 0.5rem;
    margin: 0.5rem 0;
    border: 1px solid #ccc;
    border-radius: 4px;
`;

const intToTime = (t: number) => {
  let hour = Math.floor(t % 12);
  const min = Math.round((t % 1) * 60);
  let meridian;
  if (t === 24) {
    meridian = "AM";
  } else {
    meridian = t < 12 ? "AM" : "PM";
  }
  if (hour === 0) {
    hour = 12;
  }
  const minString = min > 9 ? min : `0${min}`;
  if (min === 0) {
    return `${hour} ${meridian}`;
  }
  return `${hour}:${minString} ${meridian}`;
};

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

export function DayTimeSelector({
  minRange, maxRange, step, selectedDays, setSelectedDays, selectedTimes, setSelectedTimes, name, setName }: DayTimeSelectorProps) {

  const daysOfWeek = ["M", "T", "W", "R", "F", "S", "U"];

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

  return (
    <DayTimeFilterContainer>
      <NameRow>
        <p><strong>Name</strong></p>
        <NameInput
          type="text"
          placeholder="Break Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </NameRow>

      <DayRow>
        <p><strong>Day</strong></p>
        <FilterContainer>
          {daysOfWeek.map((day) => (
            <FilterRow key={"day-" + day}>
              <CheckboxInput
                type="checkbox"
                id={"day-" + day}
                checked={selectedDays.includes(day)}
                onChange={() => handleDayToggle(day)}
              />
              <CheckboxLabel htmlFor={"day-" + day}>{day}</CheckboxLabel>
            </FilterRow>
          ))}
        </FilterContainer>
      </DayRow>
      <Column>
        <p><strong>Time</strong></p>
        <RangeFilterContainer>
          <StyledRangeWrapper>
            <Slider
              range
              min={minRange}
              max={maxRange}
              value={selectedTimes}
              marks={{
                10.5: {
                  style: {},
                  label: intToTime(
                    selectedTimes[0]
                  ),
                },

                22: {
                  label:
                    intToTime(
                      selectedTimes[1]
                    )
                },
              }}
              step={step}
              vertical={false}
              allowCross={false}
              onChange={handleTimeChange}
            // style={{ width: "100%" }}
            />
          </StyledRangeWrapper>
        </RangeFilterContainer>
      </Column>
    </DayTimeFilterContainer>
  );
}
