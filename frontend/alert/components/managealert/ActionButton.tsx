import React from "react";
import styled from "styled-components";
import { Flex, FlexProps } from "../common/layout";
import { Img, P } from "../common/common";
import { AlertAction, WrappedStyled } from "../../types";

type ActionFlexProps = FlexProps & {
    background: string;
};

const ActionFlex: WrappedStyled<ActionFlexProps> = styled(Flex)`
    background-color: ${(props: ActionFlexProps) => props.background};
    border-radius: 0.2rem;
    cursor: pointer;
`;

const ActionButtonFlex: WrappedStyled<FlexProps> = styled(Flex)`
    & > * {
        display: block;
        margin: 0.1rem;
    }
`;

// Component associated with Resubscribe and Cancel buttons
// for each alert
interface ActionButtonProps {
    type: AlertAction;
    onClick: () => void;
}
export const ActionButton = ({ type, onClick }: ActionButtonProps) => {
    let img;
    let primary;
    let secondary;
    let text;

    switch (type) {
        case AlertAction.RESUBSCRIBE:
            primary = "#5891fc";
            secondary = "rgba(88, 145, 252, 0.12)";
            img = "/svg/bell.svg";
            text = "Resubscribe";
            break;
        case AlertAction.CANCEL:
            primary = "#646e7a";
            secondary = "rgba(162, 169, 176, 0.15)";
            img = "/svg/bell-off.svg";
            text = "Cancel";
            break;
        default:
    }

    return (
        <ActionFlex valign halign background={secondary}>
            <ActionButtonFlex valign margin="0.3rem" onClick={onClick}>
                <P size="0.6rem" color={primary} weight={600}>
                    {text}
                </P>
                <Img src={img} width="0.6rem" height="0.6rem" alt="" />
            </ActionButtonFlex>
        </ActionFlex>
    );
};
