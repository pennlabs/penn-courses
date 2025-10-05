import React from "react";
import styled from "styled-components";
import { isMobileOnly } from "react-device-detect";
import Days from "./Days";
import Times from "./Times";
import Block from "./Block";
import GridLines from "./GridLines";
import Stats from "./Stats";

import {
  Day,
  Meeting,
  Section,
  Break,
  MeetingBlock,
  FriendshipState,
  Weekdays,
  Weekends,
} from "../../types";
import { getConflictGroups } from "../meetUtil";
import { PATH_REGISTRATION_SCHEDULE_NAME } from "../../constants/constants";

const EmptyScheduleContainer = styled.div`
    font-size: 0.8em;
    text-align: center;
    margin-top: 5vh;
`;

const NoCoursesImage = styled.img`
    width: 65%;
`;

const NoCoursesAdded = styled.h3`
    font-weight: bold;
    margin-bottom: 0.5rem;
`;

const EmptySchedule = () => (
  <EmptyScheduleContainer>
    <NoCoursesImage src="/icons/empty-state-cal.svg" alt="" />
    <NoCoursesAdded>No courses added</NoCoursesAdded>
    Select courses from the cart to add them to the calendar
    <br />
  </EmptyScheduleContainer>
);

const EmptyScheduleMessage = ({ message }: { message: string }) => (
  <EmptyScheduleContainer>
    <NoCoursesImage src="/icons/empty-state-cal.svg" alt="" />
    <NoCoursesAdded>{message}</NoCoursesAdded>
    <br />
  </EmptyScheduleContainer>
);

const transformTime = (t: number) => {
  const frac = t % 1;
  const timeDec = Math.floor(t) + Math.round((frac / 0.6) * 100) / 100;
  return timeDec;
};

const ScheduleBox = styled.div`
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    color: #4a4a4a;
    display: block;
    padding: 1.25rem;
    min-height: calc(100vh - 12em);
    @media only screen and (min-width: 769px) {
        height: calc(100vh - 12em);
    }
`;

const ScheduleContents = styled.div<{ $notEmpty: boolean; $dims: any }>`
    display: grid;
    height: calc(100% - 10em);
    margin-bottom: 5px;
    margin-right: 20px;
    column-gap: 0;
    position: relative;

    background-color: white;
    font-family: "Inter";
    padding: ${({ $notEmpty, $dims }) => ($notEmpty ? $dims.padding : "1rem")};
    grid-template-columns: ${({ $notEmpty, $dims }) =>
    $notEmpty ? $dims.gridTemplateColumns : "none"};
    grid-template-rows: ${({ $notEmpty, $dims }) =>
    $notEmpty ? $dims.gridTemplateRows : "none"};

    @media only screen and (max-width: 480px) {
        height: 100%;
        max-height: 500px;
        margin-right: 0px;
    }

    @media only screen and (min-width: 480px) and (max-height: 600px) {
        height: 100%;
    }
`;

const CurrentTimeIndicator = styled.div<{
  $gridRowStart: number;
  $gridColumn: number;
  $topOffset: number;
}>`
  grid-row-start: ${({ $gridRowStart }) => Math.floor($gridRowStart)};
  grid-column: ${({ $gridColumn }) => $gridColumn};
  height: 2px;
  background-color: #ea4335;
  position: relative;
  z-index: 100;
  pointer-events: none;
  top: ${({ $topOffset }) => $topOffset}%;
  
  &::before {
    content: '';
    position: absolute;
    left: -6px;
    top: -5px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #ea4335;
  }
`;

interface ScheduleDisplayProps {
  schedName: string;
  schedData: {
    sections: Section[];
    breaks: Break[];
  };
  friendshipState: FriendshipState;
  focusSection: (id: string) => void;
  removeSection: (id: string, idType: string) => void;
  setTab?: (_: number) => void;
  readOnly: boolean;
}

const ScheduleDisplay = ({
  schedName,
  schedData,
  friendshipState,
  focusSection,
  removeSection,
  setTab,
  readOnly,
}: ScheduleDisplayProps) => {
  // actual schedule elements are offset by the row/col offset since
  // days/times take up a row/col respectively.

  if (!schedData) {
    return (
      <ScheduleBox>
        <EmptyScheduleMessage message="Loading...Standby" />
      </ScheduleBox>
    );
  }

  const rowOffset = 1;
  const colOffset = 1;

  let sections;

  sections =
    friendshipState.activeFriendSchedule?.sections ||
    schedData.sections ||
    [];

  let breaks;

  breaks = friendshipState.activeFriendSchedule?.breaks
    || schedData.breaks || [];

  const notEmpty = sections.length > 0 || breaks.length > 0;

  let startHour = 10.5;
  let endHour = 16;


  // show the weekend days only if there's a section which meets on saturday (S) or sunday (U)
  const showWeekend =
    sections.some((sec: Section) =>
      sec.meetings?.some(
        (meeting: Meeting) => meeting.day === "S" || meeting.day === "U"
      )
    ) ||
    breaks.some((brk: Break) =>
      brk.meetings?.some(
        (meeting: Meeting) => meeting.day === "S" || meeting.day === "U"
      )
    );


  // 15 minute time intervals
  const getNumRows = () => (endHour - startHour + 1) * 4 + rowOffset;
  const getNumCol = () => 5 + colOffset + (showWeekend ? 2 : 0);

  const sectionIds = sections.map((x) => x.id);

  // a meeting is the data that represents a single block on the schedule.
  const meetings: MeetingBlock[] = [];
  sections.forEach((s) => {
    if (s.meetings) {
      meetings.push(
        ...s.meetings.map((m) => ({
          day: m.day as Day,
          start: transformTime(m.start),
          end: transformTime(m.end),
          type: "section",
          course: {
            color: s.color,
            id: s.id,
            coreqFulfilled:
              s.associated_sections.length === 0 ||
              s.associated_sections.filter(
                (coreq) => sectionIds.indexOf(coreq.id) !== -1
              ).length > 0,
          },
          style: {
            width: "100%",
            left: "0",
          },
        }))
      );
    }
  });

  breaks.forEach((b: Break) => {
      if (b.meetings) {
        meetings.push(
          ...b.meetings.map((m) => ({
            day: m.day as Day,
            start: transformTime(m.start),
            end: transformTime(m.end),
            type: "break",
            course: {
              color: b.color,
              id: b.name,
              coreqFulfilled: true
            },
            style: {
              width: "100%",
              left: "0",
            },
          }))
        );
    }
  });

  startHour = Math.floor(
    Math.min(startHour, ...meetings.map((m) => m.start))
  );
  endHour = Math.ceil(Math.max(endHour, ...meetings.map((m) => m.end)));

  getConflictGroups(meetings).forEach((conflict) => {
    // for every conflict of size k, make the meetings in that conflict
    // take up (100/k) % of the square, and use `left` to place them
    // next to each other.
    const group: MeetingBlock[] = Array.from(conflict.values());
    const w = 100 / group.length;
    for (let j = 0; j < group.length; j += 1) {
      group[j].style = {
        width: `${w}%`,
        left: `${w * j}%`,
      };
    }
  });

  const dims = {
    gridTemplateColumns: `.4fr repeat(${getNumCol() - 1}, 1fr)`,
    gridTemplateRows: `repeat(${getNumRows() - 2}, 1fr)`,
    padding: isMobileOnly ? "0.2rem" : "1rem",
  };

  // Calculate current time indicator position
  const getCurrentTimeIndicatorPosition = () => {
    if (!notEmpty) return null;

    const now = new Date();
    let currentHour = now.getHours() + now.getMinutes() / 60;
    let dayOfWeek = now.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday

    // Map JavaScript day of week to schedule days
    const dayMap: { [key: number]: Day | null } = {
      0: Weekends.U, // Sunday
      1: Weekdays.M, // Monday
      2: Weekdays.T, // Tuesday
      3: Weekdays.W, // Wednesday
      4: Weekdays.R, // Thursday
      5: Weekdays.F, // Friday
      6: Weekends.S, // Saturday
    };

    const currentDay = dayMap[dayOfWeek];

    // Don't show indicator if there is nothing in the weekend
      const showWeekend =
          sections.some((sec: Section) =>
              sec.meetings?.some(
                  (meeting: Meeting) => meeting.day === "S" || meeting.day === "U"
              )
          ) ||
          breaks.some((brk: Break) =>
              brk.meetings?.some(
                  (meeting: Meeting) => meeting.day === "S" || meeting.day === "U"
              )
          );
      if (!showWeekend && (currentDay === Weekends.S || currentDay === Weekends.U)) {
          return null;
      }


    // Don't show if current time is outside schedule range
    if (currentHour < startHour || currentHour > endHour) {
      return null;
    }

    // Find the column index for the current day
    const days = [Weekdays.M, Weekdays.T, Weekdays.W, Weekdays.R, Weekdays.F, Weekends.S, Weekends.U];
    const dayIndex = days.indexOf(currentDay as Weekdays);

    if (dayIndex === -1) return null;

    // Calculate grid position (grid uses 15-minute intervals, 4 rows per hour)
    // Instead of snapping to grid lines, calculate the exact position
    const timeFromStart = currentHour - startHour;
    const rowsFromStart = timeFromStart * 4; // Total rows as a decimal
    const gridRowStart = Math.floor(rowsFromStart) + rowOffset + 1;
    const topOffset = (rowsFromStart % 1) * 100; // Percentage offset within the grid row
    const gridColumn = dayIndex + 1 + colOffset;

    return { gridRowStart, gridColumn, topOffset };
  };

  const timeIndicatorPos = getCurrentTimeIndicatorPosition();

  return (
    <ScheduleBox>
      <ScheduleContents $dims={dims} $notEmpty={notEmpty}>
        {notEmpty && <Days offset={colOffset} weekend={showWeekend} />}
        {notEmpty && (
          <Times
            startTime={startHour}
            endTime={endHour}
            numRow={getNumRows() - 2}
            offset={rowOffset}
          />
        )}
        {notEmpty && (
          <GridLines numRow={getNumRows()} numCol={getNumCol()} />
        )}
        {notEmpty &&
          meetings &&
          meetings.map((meeting) => (
            <Block
              meeting={meeting}
              course={meeting.course}
              style={meeting.style}
              offsets={{
                time: startHour,
                row: rowOffset,
                col: colOffset,
              }}
              readOnly={readOnly}
              remove={() => removeSection(meeting.course.id, meeting.type)}
              key={`${meeting.course.id}-${meeting.day}`}
              focusSection={meeting.type == "section" ? () => {
                if (isMobileOnly && setTab) {
                  setTab(0);
                }
                const split = meeting.course.id.split("-");
                focusSection(`${split[0]}-${split[1]}`);
              } : () => { }}
            />
          ))}
        {/* Current Time Indicator - only shows on weekdays */}
        {timeIndicatorPos && (
          <CurrentTimeIndicator
            $gridRowStart={timeIndicatorPos.gridRowStart}
            $gridColumn={timeIndicatorPos.gridColumn}
            $topOffset={timeIndicatorPos.topOffset}
          />
        )}
        {!notEmpty && !readOnly && <EmptySchedule />}
        {!notEmpty &&
          readOnly &&
          friendshipState.activeFriendSchedule &&
          !friendshipState.activeFriendSchedule.found && (
            <EmptyScheduleMessage message="Your friend is not sharing a schedule yet" />
          )}
        {!notEmpty &&
          readOnly &&
          friendshipState.activeFriendSchedule?.found && (
            <EmptyScheduleMessage message="Your friend has not added courses to their schedule yet" />
          )}
        {!notEmpty &&
          readOnly &&
          schedName == PATH_REGISTRATION_SCHEDULE_NAME && (
            <EmptyScheduleMessage message="Penn Course Plan doesn't have your course registration data (yet!)." />
          )}
      </ScheduleContents>
      {notEmpty && <Stats meetings={sections} />}
    </ScheduleBox>
  );
};

export default ScheduleDisplay;
