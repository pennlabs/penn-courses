import React from "react";
import styled from "styled-components";
import {
    GridItem,
    GridCourseTitle,
} from "pcx-shared-components/src/common/layout";

const GridSubtitle = styled.div`
    color: #282828;
    font-size: 0.9rem;
    padding-top: 0.4rem;
    font-family: "Inter", sans-serif;
    font-weight: bold;
    white-space: nowrap;
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
            {Array.from({ length: 7 }, (_, index) => (
                <GridItem
                    column={index + 2}
                    row={rownum}
                    border
                    halign
                    valign
                    talign
                />
            ))}
        </>
    );
};
