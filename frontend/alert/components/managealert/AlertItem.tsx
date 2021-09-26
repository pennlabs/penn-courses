import React from "react";
import styled from "styled-components";
import { GridItem } from "pcx-shared-components/src/common/layout";
import { P } from "../common/common";
import { ActionButton } from "./ActionButton";
import { AlertAction, AlertRepeat, SectionStatus } from "../../types";

const StatusInd = styled.div<{ background: string }>`
    border-radius: 1rem;
    width: 0.4rem;
    height: 0.4rem;
    background-color: ${(props) => props.background};
`;

const StatusGridItem = styled(GridItem)`
    & > * {
        display: block;
        margin: 0.2rem;
    }
`;

// Component for an alert entry (renders as a row in CSS grid)
interface AlertItemProps {
    alertLastSent: string;
    course: string;
    status: SectionStatus;
    repeat: AlertRepeat;
    actions: AlertAction;
    rownum: number;
    checked: boolean;
    toggleAlert: () => void;
    actionButtonHandler: () => void;
}
export const AlertItem = ({
    alertLastSent,
    course,
    status,
    repeat,
    actions,
    rownum,
    checked,
    toggleAlert,
    actionButtonHandler,
}: AlertItemProps) => {
    let statustext;
    let statuscolor;
    let alerttext;
    let alertcolor;

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

    switch (repeat) {
        case AlertRepeat.INACTIVE:
            alerttext = "Inactive";
            alertcolor = "#b2b2b2";
            break;
        case AlertRepeat.EOS:
            alerttext = "Until end of semester";
            alertcolor = "#333333";
            break;
        case AlertRepeat.ONCE:
            alerttext = "Once";
            alertcolor = "#333333";
            break;
        default:
    }

    return (
        <>
            <GridItem column={1} row={rownum} border halign valign>
                <input
                    type="checkbox"
                    checked={checked}
                    onChange={toggleAlert}
                />
            </GridItem>
            <GridItem column={2} row={rownum} border valign>
                {alertLastSent ? (
                    <P size="0.7rem">{alertLastSent}</P>
                ) : (
                    <P size="0.7rem" color="#b2b2b2">
                        No alerts sent yet
                    </P>
                )}
            </GridItem>
            <GridItem column={3} row={rownum} border valign>
                <P size="0.7rem">{course}</P>
            </GridItem>
            <StatusGridItem column={4} row={rownum} border valign>
                <StatusInd background={statuscolor} />
                <P size="0.7rem">{statustext}</P>
            </StatusGridItem>
            <GridItem column={5} row={rownum} border valign>
                <P size="0.7rem" color={alertcolor}>
                    {alerttext}
                </P>
            </GridItem>
            <GridItem border column={6} row={rownum} valign>
                <ActionButton type={actions} onClick={actionButtonHandler} />
            </GridItem>
        </>
    );
};
