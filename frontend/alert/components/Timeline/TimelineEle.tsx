import React, { useState, useEffect } from "react";
import styled from "styled-components";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCircle } from "@fortawesome/free-solid-svg-icons";

//const to calculate segment length
const MIN_SEGMENT_LENGTH = 20;
const MAX_SEGMENT_LENGTH = 250;
const MULTIPLIER = 18;

const Circle = styled.div<{ open: boolean }>`
    height: 0.875rem;
    width: 0.875rem;
    border: 0.0625rem solid ${({ open }) => (open ? "#78D381" : "#cbd5dd")};
    border-radius: 50%;
    color: ${({ open }) => (open ? "#78D381" : "#cbd5dd")};
    font-size: 0.625rem;
    text-align: center;
    vertical-align: middle;
    line-height: 0.875rem;
`;

type SegmentProps = {
    open: boolean;
    length: number;
};

const Segment = styled.div<SegmentProps>`
    background-color: ${({ open }) => (open ? "#78D381" : "#cbd5dd")};
    height: ${({ length }) => length}px;
    width: 0.1875rem;
`;

type InfoLabelProps = {
    isTime?: boolean | false;
};

const InfoLabel = styled.div<InfoLabelProps>`
    font-size: 0.9375rem;
    color: rgba(40, 40, 40, 1);
    height: 0.875rem;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    justify-self: ${({ isTime }) => (isTime ? "end" : "start")};
`;

const convertTime = (timeString) => {
    /* Convert time string to array with MM/DD as
     * the first element and HR:MIN pm/am as the second
     */
    let d = new Date(timeString);

    //format: ["MM:DD", "HR:MIN pm/am"]
    return [
        d.toLocaleDateString("en-US", { month: "numeric", day: "numeric" }),
        d
            .toLocaleTimeString("en-US", {
                hour12: true,
                hour: "numeric",
                minute: "numeric",
            })
            .toLowerCase(),
    ];
};

const timeInHours = (timeString) => {
    let d = new Date(timeString);
    return d.getHours();
};

interface TimelineEleProps {
    courseStatusData: any;
    index: number;
}

const TimelineEle = ({ courseStatusData, index }: TimelineEleProps) => {
    const prevTime = courseStatusData[index - 1][0]["created_at"];
    const currTime = courseStatusData[index][0]["created_at"];
    const segLength = Math.min(
        Math.round(
            MIN_SEGMENT_LENGTH +
                Math.abs(timeInHours(prevTime) - timeInHours(currTime)) *
                    MULTIPLIER
        ),
        MAX_SEGMENT_LENGTH
    );

    return (
        <>
            {index - 1 == 0 ? (
                <>
                    <InfoLabel>{convertTime(prevTime)[0]}</InfoLabel>
                    <Segment
                        open={courseStatusData[index - 1][1] == "opened"}
                        length={segLength}
                    />
                    <InfoLabel isTime={true}>
                        {convertTime(prevTime)[1]}
                    </InfoLabel>
                </>
            ) : (
                <>
                    <div></div>
                    <Segment
                        open={courseStatusData[index - 1][1] == "opened"}
                        length={segLength}
                    />
                    <div></div>
                </>
            )}

            <InfoLabel>
                {!courseStatusData[index][2] && convertTime(currTime)[0]}
            </InfoLabel>
            <Circle open={courseStatusData[index][1] == "opened"}>
                <FontAwesomeIcon icon={faCircle} />
            </Circle>
            <InfoLabel isTime={true}>{convertTime(currTime)[1]}</InfoLabel>
        </>
    );
};

export default TimelineEle;
