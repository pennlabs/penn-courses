import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import { GridItem, P } from "./ManageAlertStyledComponents";
import { ActionButton } from "./ActionButton";
import { AlertStatus, AlertAction, AlertRepeat } from "./AlertItemEnums";

const StatusInd = styled.div`
    border-radius: 1rem;
    width: 0.4rem;
    height: 0.4rem;
    background-color: ${props => props.background};
`;

const StatusGridItem = styled(GridItem)`
    & > * {
        display: block;
        margin: 0.2rem;
    }
`;

// Component for an alert entry (renders as a row in CSS grid)
export const AlertItem = ({
    date, course, status, repeat, actions, rownum, checked, toggleAlert, actionHandler
}) => {
    let statustext;
    let statuscolor;
    let alerttext;
    let alertcolor;

    switch (status) {
        case "closed":
            statustext = "Closed";
            statuscolor = "#e1e6ea";
            break;
        case "open":
            statustext = "Open";
            statuscolor = "#78d381";
            break;
        default:
    }

    switch (repeat) {
        case "inactive":
            alerttext = "Inactive";
            alertcolor = "#b2b2b2";
            break;
        case "eos":
            alerttext = "Until end of semester";
            alertcolor = "#333333";
            break;
        case "once":
            alerttext = "Once";
            alertcolor = "#333333";
            break;
        default:
    }


    return (
        <>
            <GridItem column="1" row={rownum} border halign valign>
                <input type="checkbox" checked={checked} onChange={toggleAlert} />
            </GridItem>
            <GridItem column="2" row={rownum} border valign>
                {
                    date
                        ? <P size="0.7rem">{date}</P>
                        : (
                            <P
                                size="0.7rem"
                                color="#b2b2b2"
                            >
                                No alerts sent yet
                            </P>
                        )
                }
            </GridItem>
            <GridItem column="3" row={rownum} border valign>
                <P size="0.7rem">{course}</P>
            </GridItem>
            <StatusGridItem column="4" row={rownum} border valign>
                <StatusInd background={statuscolor} />
                <P size="0.7rem">{statustext}</P>
            </StatusGridItem>
            <GridItem column="5" row={rownum} border valign>
                <P size="0.7rem" color={alertcolor}>{alerttext}</P>
            </GridItem>
            <GridItem border column="6" row={rownum} valign>
                <ActionButton type={actions} onClick={actionHandler} />
            </GridItem>
        </>
    );
};

AlertItem.propTypes = {
    date: PropTypes.string,
    course: PropTypes.string,
    status: PropTypes.oneOf([AlertStatus.Closed, AlertStatus.Open]),
    repeat: PropTypes.oneOf([AlertRepeat.EOS, AlertRepeat.Inactive, AlertRepeat.Once]),
    actions: PropTypes.oneOf([AlertAction.Resubscribe, AlertAction.Cancel]),
    rownum: PropTypes.number,
};
