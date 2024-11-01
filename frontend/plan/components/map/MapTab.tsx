import React, { useState } from "react";
import { connect } from "react-redux";
import dynamic from "next/dynamic";
import styled from "styled-components";
import MapDropdown from "./MapDropdown";
import MapCourseItem from "./MapCourseItem";
import { scheduleContainsSection } from "../meetUtil";
import { DAYS_TO_DAYSTRINGS } from "../../constants/constants";
import { Section, Meeting, Day } from "../../types";
import "leaflet/dist/leaflet.css";
import { ThunkDispatch } from "redux-thunk";
import { fetchCourseDetails } from "../../actions";

const Map = dynamic(() => import("./Map"), {
    ssr: false,
});

const Box = styled.section<{ $length: number }>`
    position: relative;
    height: calc(100vh - 9em - 3em);
    border-radius: 4px;
    box-shadow: 0 5px 14px 0 rgba(0, 0, 0, 0.09);
    background-color: white;
    color: #4a4a4a;
    overflow: ${(props) => (props.$length === 0 ? "hidden" : "auto")};
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

const MapContainer = styled.div`
    height: 40%;
    padding-left: 7px;
    padding-right: 7px;
    margin-right: 5px;
    margin-top: 5px;
`;

interface MabTapProps {
    meetingsByDay: Record<Day, Meeting[]>;
    focusSection: (id: string) => void;
}

const CartEmptyImage = styled.img`
    max-width: min(60%, 40vw);
`;

interface DayEmptyProps {
    day: Day;
}

const DayEmpty = ({ day }: DayEmptyProps) => (
    <div
        style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
        }}
    >
        <h3
            style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
        >
            {`You don't have classes on ${DAYS_TO_DAYSTRINGS[day as Day]}!`}
        </h3>
        Click a course section&apos;s + icon to add it to the schedule.
        <br />
        <CartEmptyImage src="/icons/empty-state-cart.svg" alt="" />
    </div>
);

function MapTab({ meetingsByDay, focusSection }: MabTapProps) {
    const [selectedDay, setSelectedDay] = useState<Day>(Day.M);
    const meeetingsForDay = meetingsByDay[selectedDay];

    return (
        <Box $length={meeetingsForDay.length} id="cart">
            <MapDropdown
                selectedDay={selectedDay}
                setSelectedDay={setSelectedDay}
            />
            {meeetingsForDay.length === 0 ? (
                <DayEmpty day={selectedDay} />
            ) : (
                <>
                    <MapContainer>
                        <Map
                            locations={meeetingsForDay
                                .map((meeting: Meeting) => ({
                                    lat: meeting.latitude,
                                    lng: meeting.longitude,
                                }))
                                .filter(
                                    (locData) =>
                                        locData.lat != null &&
                                        locData.lng != null
                                )}
                            zoom={15}
                        />
                    </MapContainer>
                    {meeetingsForDay.map(
                        (
                            {
                                id,
                                latitude,
                                longitude,
                                start,
                                end,
                                room,
                                overlap,
                            }: Meeting,
                            i: number
                        ) => {
                            return (
                                <MapCourseItem
                                    key={id + i} // handle same class more than once/day (e.g. PHYS)
                                    id={id}
                                    lat={latitude}
                                    lng={longitude}
                                    start={start}
                                    end={end}
                                    room={room}
                                    overlap={overlap!}
                                    focusSection={focusSection}
                                />
                            );
                        }
                    )}
                </>
            )}
        </Box>
    );
}

function getMeetingsByDay(schedules: any, scheduleSelected: any) {
    const meetingsByDay: Record<Day, Meeting[]> = {
        M: [],
        T: [],
        W: [],
        R: [],
        F: [],
        S: [],
        U: [],
    };

    const sections = schedules.Schedule.sections;

    sections.forEach((section: Section) => {
        const inCart =
            schedules[scheduleSelected] &&
            scheduleContainsSection(
                schedules[scheduleSelected].sections,
                section
            );

        if (inCart) {
            section.meetings?.forEach((meeting: Meeting) => {
                const day = meeting.day;
                meetingsByDay[day as Day].push({
                    id: section.id,
                    start: meeting.start,
                    end: meeting.end,
                    latitude: meeting.latitude,
                    longitude: meeting.longitude,
                    room: meeting.room,
                    overlap: false,
                });
            });
        }
    });

    Object.keys(meetingsByDay).forEach((day) => {
        meetingsByDay[day as Day]
            .sort(
                (a: Meeting, b: Meeting) => a.start - b.start || a.end - b.end
            )
            .forEach((meeting, index, arr) => {
                const currentMeeting = meeting;
                const nextMeeting = arr[index + 1];

                if (nextMeeting && currentMeeting.end > nextMeeting.start) {
                    currentMeeting.overlap = true;
                    nextMeeting.overlap = true;
                } else {
                    currentMeeting.overlap = currentMeeting.overlap || false;
                }
            });
    });

    return meetingsByDay;
}

const mapStateToProps = ({
    schedule: { schedules, scheduleSelected },
}: any) => ({
    meetingsByDay: schedules.Schedule
        ? getMeetingsByDay(schedules, scheduleSelected)
        : {
              M: [],
              T: [],
              W: [],
              R: [],
              F: [],
              S: [],
              U: [],
          },
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    focusSection: (id: string) => dispatch(fetchCourseDetails(id)),
});

export default connect(mapStateToProps, mapDispatchToProps)(MapTab);
