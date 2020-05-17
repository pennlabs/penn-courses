import React from "react";
import styled from "styled-components";
import PropTypes from "prop-types";
import Bell from "../../assets/bell.svg";
import XBell from "../../assets/bell-off.svg";
import { Flex } from "../common/layout";
import { Img, P } from "../common/common";
import { AlertAction } from "./AlertItemEnums";

const ActionFlex = styled(Flex)`
    background-color: ${props => props.background};
    border-radius: 0.2rem;
    cursor: pointer;
`;

const ActionButtonFlex = styled(Flex)`
    & > * {
        display: block;
        margin: 0.1rem;
    }
`;

// Component associated with Resubscribe and Cancel buttons
// for each alert
export const ActionButton = ({ type, onClick }) => {
    let img;
    let primary;
    let secondary;
    let text;

    switch (type) {
        case "resub":
            primary = "#5891fc";
            secondary = "rgba(88, 145, 252, 0.12)";
            img = Bell;
            text = "Resubscribe";
            break;
        case "cancel":
            primary = "#646e7a";
            secondary = "rgba(162, 169, 176, 0.15)";
            img = XBell;
            text = "Cancel";
            break;
        default:
    }

    return (
        <ActionFlex valign halign background={secondary}>
            <ActionButtonFlex valign margin="0.3rem" onClick={onClick}>
                <P size="0.6rem" color={primary} weight="600">{text}</P>
                <Img src={img} width="0.6rem" height="0.6rem" alt="" />
            </ActionButtonFlex>
        </ActionFlex>
    );
};

ActionButton.propTypes = {
    type: PropTypes.oneOf([AlertAction.Resubscribe, AlertAction.Cancel]),
    onClick: PropTypes.func,
};
