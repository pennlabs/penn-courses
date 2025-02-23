import React from "react";
import styled from "styled-components";
import { useSelector } from "react-redux";
import scrollIntoView from "scroll-into-view-if-needed";
import Badge from "../Badge";
import { getTimeString, meetingSetsIntersect } from "../meetUtil";
import { Section as SectionType } from "../../types";
import AlertButton from "../alert/AlertButton";

interface SectionProps {
    section: SectionType;
    cart: {
        add: () => void;
        remove: () => void;
    };
    toggleMap: {
        open: (room: string, latitude: number, longitude: number) => void;
    };
    inCart: boolean;
    alerts: {
        add: () => void;
        remove: () => void;
    };
    inAlerts: boolean;
}

const SectionContainer = styled.div`
    transition: 250ms;
    &:hover {
        background-color: rgba(105, 117, 244, 0.05);
    }
`;

const SectionInfoContainer = styled.li`
    display: flex;
    align-items: center;
    margin-bottom: 0;
    border-bottom: 1px solid rgb(230, 230, 230);
    overflow-x: scroll;
    -ms-overflow-style: none; /* Internet Explorer 10+ */
    scrollbar-width: none; /* Firefox */

    &::-webkit-scrollbar {
        display: none;
    }
`;

const SectionInfo = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    flex-grow: 1;
    justify-content: space-between;
    padding: 1em;
    padding-right: 0;
`;

const IdAndInstructorContainer = styled.div`
    display: flex;
    justify-content: space-between;
    align-items: center;
`;

const IdAndActivityContainer = styled.div`
    font-size: 1rem;
    font-weight: bold;
    margin-right: 1.5em;
    display: flex;
    align-items: center;
`;

const ActivityType = styled.span`
    font-size: 0.7rem;
    margin-left: 0.5em;
    font-weight: normal;
`;

const InstructorContainer = styled.div`
    font-size: 0.85rem;
    font-weight: bold;
    text-overflow: ellipsis;
    flex-grow: 6;
`;

const MiscellaneousInfoContainer = styled.div`
    min-width: 200px;
    margin-top: 0.5em;
    display: grid;
    font-size: 0.7rem;
    grid-template-columns: 39% 15% 46%;
`;

const BadgesContainer = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
`;

const AddRemoveButton = styled.div`
    padding: 1.8em 1.8em 1.8em 1em;
    width: 2.5em;

    .fas {
        cursor: pointer;
    }

    .fa-times {
        color: rgba(0, 0, 0, 0.2);
        transition: 200ms ease color;
    }

    &:hover .fa-times {
        color: rgba(0, 0, 0, 0.33);
    }
`;

const HoverSwitch = styled.div`
    .fa-check {
        color: #3daa6d;
    }

    &:hover .fa-check,
    & .fa-times {
        display: none;
    }

    &:hover .fa-times {
        display: inline;
    }
`;

export default function Section({
    section,
    cart,
    inCart,
    toggleMap,
    alerts,
    inAlerts,
}: SectionProps) {
    const { instructors, meetings, status } = section;

    const { schedules, scheduleSelected } = useSelector(
        (store: any) => store.schedule
    );

    const overlap =
        meetings && schedules[scheduleSelected]
            ? meetingSetsIntersect(
                  meetings,
                  schedules[scheduleSelected].sections
                      .filter((s: SectionType) => s.id !== section.id)
                      .map((s: SectionType) => s.meetings)
                      .flat()
              )
            : false;

    const cartAdd = () => {
        cart.add();
        setTimeout(() => {
            const target = document.getElementById(section.id);
            if (target !== null) {
                scrollIntoView(target, {
                    behavior: "smooth",
                    block: "end",
                    scrollMode: "if-needed",
                });
            }
        }, 50);
    };

    const cleanedMeetings =
        meetings &&
        Array.from(
            new Map(
                meetings
                    .filter(({ room }) => room)
                    .map(({ room, latitude, longitude }) => [
                        room.trim(),
                        { room: room.trim(), latitude, longitude },
                    ])
            ).values()
        );

    return (
        <SectionContainer>
            <SectionInfoContainer
                onClick={inCart ? cart.remove : () => cartAdd()}
            >
                <SectionInfo>
                    <IdAndInstructorContainer>
                        <IdAndActivityContainer>
                            {`${section.id.split("-").pop()} `}
                            <ActivityType>{section.activity}</ActivityType>
                        </IdAndActivityContainer>
                        <InstructorContainer>
                            {instructors.length > 0 ? (
                                <>
                                    {instructors.map((elem, ind) => (
                                        <div key={elem.id}>
                                            {ind !== 0 ? <br /> : null}
                                            {ind !== instructors.length - 1
                                                ? `${elem.name},`
                                                : elem.name}
                                        </div>
                                    ))}
                                </>
                            ) : (
                                <div> N/A </div>
                            )}
                        </InstructorContainer>
                    </IdAndInstructorContainer>
                    <MiscellaneousInfoContainer>
                        <div style={{ paddingRight: "5px" }}>
                            {overlap && (
                                <div className="popover is-popover-right">
                                    <i
                                        style={{
                                            paddingRight: "5px",
                                            color: "#c6c6c6",
                                        }}
                                        className="fas fa-calendar-times"
                                    />
                                    <span className="popover-content">
                                        Conflicts with schedule!
                                    </span>
                                </div>
                            )}
                            {meetings && getTimeString(meetings)}
                        </div>
                        <div>{`${section.credits} CU`}</div>
                        <div>
                            {cleanedMeetings && cleanedMeetings.length > 0 ? (
                                <div style={{ display: "flex" }}>
                                    <i
                                        className="fas fa-map-marker-alt grey-text"
                                        style={{ color: "#c6c6c6" }}
                                    />
                                    &nbsp;
                                    <div style={{ display: "flex" }}>
                                        {cleanedMeetings.map(
                                            (
                                                { room, latitude, longitude },
                                                i
                                            ) => (
                                                <div key={room}>
                                                    {latitude ? (
                                                        <span
                                                            onClick={() =>
                                                                toggleMap.open(
                                                                    room,
                                                                    latitude,
                                                                    longitude
                                                                )
                                                            }
                                                            style={{
                                                                color:
                                                                    "#878ED8",
                                                                textDecoration:
                                                                    "underline",
                                                                cursor:
                                                                    "pointer",
                                                            }}
                                                        >
                                                            {room}
                                                        </span>
                                                    ) : (
                                                        <span>{room}</span>
                                                    )}
                                                    {i <
                                                        cleanedMeetings.length -
                                                            1 && (
                                                        <span>,&nbsp;</span>
                                                    )}
                                                </div>
                                            )
                                        )}
                                    </div>
                                </div>
                            ) : null}
                        </div>
                    </MiscellaneousInfoContainer>
                </SectionInfo>
                <BadgesContainer>
                    <div>
                        {instructors.length > 0 ? (
                            <div className="popover is-popover-left">
                                <Badge value={section.instructor_quality} />
                                <span className="popover-content">
                                    Instructor Quality
                                </span>
                            </div>
                        ) : (
                            <Badge value={section.instructor_quality} />
                        )}
                    </div>
                    {status === "C" ? (
                        <div className={`popover is-popover-left`}>
                            <AlertButton alerts={alerts} inAlerts={inAlerts} />

                            {inAlerts || (
                                <span className="popover-content">
                                    {" "}
                                    Course is closed. Sign up for an alert!{" "}
                                </span>
                            )}
                        </div>
                    ) : (
                        <div />
                    )}
                </BadgesContainer>
                <AddRemoveButton
                    role="button"
                    onClick={(event) => {
                        event.stopPropagation();
                        inCart ? cart.remove() : cartAdd();
                    }}
                >
                    {inCart ? (
                        <HoverSwitch>
                            <i className="fas fa-check" />
                            <i className="fas fa-times" />
                        </HoverSwitch>
                    ) : (
                        <i
                            className="fas fa-plus"
                            style={{ color: "#c6c6c6" }}
                        />
                    )}
                </AddRemoveButton>
            </SectionInfoContainer>
        </SectionContainer>
    );
}
