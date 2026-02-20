import React from "react";
import styled from "styled-components";
import { GridItem } from "pcx-shared-components/src/common/layout";
import { P } from "../common/common";
import ToggleSwitch from "../common/ToggleSwitch";
import { AlertAction, SectionStatus } from "../../types";
import { Img } from "../common/common";

const StatusInd = styled.div<{ $background: string }>`
    border-radius: 1rem;
    width: 0.4rem;
    height: 0.4rem;
    background-color: ${(props) => props.$background};
`;

const StatusGridItem = styled(GridItem)`
    & > * {
        display: flex;
        margin: 0.2rem;
    }
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
    
`

// Component for an alert entry (renders as a row in CSS grid)
interface AlertItemProps {
    alertLastSent: string;
    course: string;
    status: SectionStatus;
    actions: AlertAction;
    closed: AlertAction;
    rownum: number;
    checked: boolean;
    toggleAlert: () => void;
    alertHandler: () => void;
    closedHandler: () => void;
    deleteHandler: () => void;
}
export const AlertItem = ({
    alertLastSent,
    course,
    status,
    actions,
    closed,
    rownum,
    checked,
    toggleAlert,
    alertHandler,
    closedHandler,
    deleteHandler,
}: AlertItemProps) => {
    let statustext;
    let statuscolor;

    switch (status) {
        case SectionStatus.CLOSED:
            statustext = "Closed";
            statuscolor = "#e1e6ea";
            break;
        case SectionStatus.OPEN:
            statustext = "Open";
            statuscolor = "#78d381";
            break;
        default:
    }

    return (
        <>
            <GridItem $column={1} $row={rownum} $border $halign $valign>
                <input
                    type="checkbox"
                    checked={checked}
                    onChange={toggleAlert}
                />
            </GridItem>
            <GridItem $column={2} $row={rownum} $border $halign $valign $talign>
                {alertLastSent ? (
                    <P $size="0.7rem">{alertLastSent}</P>
                ) : (
                    <P $size="0.7rem" $color="#b2b2b2">
                        No alerts sent yet
                    </P>
                )}
            </GridItem>
            <GridItem $column={3} $row={rownum} $border $halign $valign $talign>
                <P $size="0.7rem">{course}</P>
            </GridItem>
            <StatusGridItem $column={4} $row={rownum} $border $halign $valign>
                <StatusInd $background={statuscolor} />
                <P $size="0.7rem">{statustext}</P>
            </StatusGridItem>
            <GridItem $border $column={5} $row={rownum} $halign $valign></GridItem>
            <GridItem $border $column={6} $row={rownum} $halign $valign>
                <ToggleSwitch type={actions} handleChange={alertHandler} />
            </GridItem>
            <GridItem $border $column={7} $row={rownum} $halign $valign>
                <ToggleSwitch type={closed} handleChange={closedHandler} />
            </GridItem>
            <GridItem $border $column={8} $row={rownum} $halign $valign>
                <TrashImg
                    src="/svg/trash.svg"
                    width="1.15rem"
                    height="1.15rem"
                    onClick={deleteHandler}
                />
            </GridItem>
        </>
    );
};
