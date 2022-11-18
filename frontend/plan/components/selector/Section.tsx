import React from "react";
import styled from "styled-components";
import { useSelector } from "react-redux";
import scrollIntoView from "scroll-into-view-if-needed";

import Badge from "../Badge";

import { getTimeString, meetingSetsIntersect } from "../meetUtil";
import { Section as SectionType } from "../../types";

interface SectionProps {
    section: SectionType;
    cart: {
        add: () => void;
        remove: () => void;
    };
    inCart: boolean;
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
    -ms-overflow-style: none;  /* Internet Explorer 10+ */
    scrollbar-width: none;  /* Firefox */

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

const Bell = styled.a`
    color: gray;
    &:hover {
        color: #669afb;
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

export default function Section({ section, cart, inCart }: SectionProps) {
    const { instructors, meetings, status } = section;

    const { schedules, scheduleSelected } = useSelector(
        (store: any) => store.schedule
    );

    const overlap = meetings
        ? meetingSetsIntersect(
              meetings,
              schedules[scheduleSelected].meetings
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
    const cleanedRooms =
        meetings &&
        Array.from(
            new Set(
                meetings
                    .filter(({ room }) => room)
                    .map(({ room }) => room.trim())
            )
        );
    return (
        <SectionContainer>
            <SectionInfoContainer onClick={inCart ? cart.remove : () => cartAdd()}>
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
                            {cleanedRooms && cleanedRooms.length > 0 ? (
                                <div>
                                    <i
                                        className="fas fa-map-marker-alt grey-text"
                                        style={{ color: "#c6c6c6" }}
                                    />
                                    &nbsp;
                                    {cleanedRooms.join(", ")}
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
                        <div className="popover is-popover-left">
                            <Bell
                                target="_blank"
                                rel="noopener noreferrer"
                                href={`https://penncoursealert.com/?course=${section.id}`}
                                onClick={(event) => {
                                    event.stopPropagation();
                                }}
                            >
                                <i
                                    style={{ fontSize: "1rem" }}
                                    className="far fa-bell"
                                />
                            </Bell>

                            <span className="popover-content">
                                {" "}
                                Course is closed. Sign up for an alert!{" "}
                            </span>
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
