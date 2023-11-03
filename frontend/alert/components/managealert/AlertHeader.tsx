import React from "react";
import styled from "styled-components";
import {
    GridItem,
    GridCourseTitle,
} from "pcx-shared-components/src/common/layout";
import { P } from "../common/common";
import ToggleSwitch from "../common/ToggleSwitch";
import { AlertAction, SectionStatus } from "../../types";
import { Img } from "../common/common";
import { configureScope } from "@sentry/browser";
import { Flex } from "pcx-shared-components/src/common/layout";

const GridTitle = styled.div`
    color: #282828;
    font-size: 1rem;
    font-family: "Inter", sans-serif;
    font-weight: bold;
    padding-top: 0.5rem;
`;

const GridSubtitle = styled.div`
    color: #282828;
    font-size: 0.9rem;
    padding-top: 0.4rem;
    font-family: "Inter", sans-serif;
    font-weight: bold;
    white-space: nowrap;
`;

const TrashImg = styled(Img)`
    cursor: pointer;
    opacity: 75%;

    &:hover {
        opacity: 100%;
    }
    &:active {
        transform: translateY(0.1rem);
    }
`;

// Component for an alert entry (renders as a row in CSS grid)
interface AlertHeaderProps {
    course: string;
    rownum: number;
}
export const AlertHeader = ({ course, rownum }: AlertHeaderProps) => {
    return (
        <>
            <GridCourseTitle column={1} valign border>
                <GridSubtitle>{course.toUpperCase()}</GridSubtitle>
            </GridCourseTitle>

            {/* used to make sure grid line goes to end */}
            <GridItem
                column={2}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
            <GridItem
                column={3}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
            <GridItem
                column={4}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
            <GridItem
                column={5}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
            <GridItem
                column={6}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
            <GridItem
                column={7}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
            <GridItem
                column={8}
                row={rownum}
                border
                halign
                valign
                talign
            ></GridItem>
        </>
    );
};
