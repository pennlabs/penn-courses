import React from "react";
import styled from "styled-components";
import scrollIntoView from "scroll-into-view-if-needed";

import Badge from "../Badge";

import { getTimeString } from "../meetUtil";
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
    margin-right: 1em;
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
    grid-template-columns: 40% 15% 40%;
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
`;

export default function Section({ section, cart, inCart }: SectionProps) {
    const { instructors, meetings, status } = section;
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
    return (
        <SectionContainer>
            <SectionInfoContainer>
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
                        <div>{meetings && getTimeString(meetings)}</div>
                        <div>{`${section.credits} CU`}</div>
                        <div>
                            {meetings && meetings.length > 0 ? (
                                <div>
                                    <i className="fas fa-map-marker-alt grey-text" />
                                    &nbsp;
                                    {((l) => {
                                        // formats location names
                                        const ret = new Set();
                                        l.forEach(({ room }) =>
                                            ret.add(room.trim())
                                        );
                                        return Array.from(ret);
                                    })(meetings).join(", ")}
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
                            <a
                                className="bell"
                                target="_blank"
                                rel="noopener noreferrer"
                                href={`https://penncoursealert.com/?course=${section.id}`}
                            >
                                <i
                                    style={{ fontSize: "1rem" }}
                                    className="far fa-bell"
                                />
                            </a>

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
                    onClick={inCart ? cart.remove : () => cartAdd()}
                >
                    {inCart ? (
                        <div className="hover-switch">
                            <i className="fas fa-check" />
                            <i className="fas fa-times" />
                        </div>
                    ) : (
                        <i className="fas fa-plus" />
                    )}
                </AddRemoveButton>
            </SectionInfoContainer>
        </SectionContainer>
    );
}
