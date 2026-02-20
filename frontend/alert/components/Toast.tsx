import React, { PropsWithChildren } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import {
    FontAwesomeIcon,
} from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

import { between, TABLET, SMALLDESKTOP } from "../constants";

interface BorderProps {
    $border: string;
    $background: string;
}

const Rectangle = styled.div<BorderProps>`
    display: flex;
    flex-direction: row;
    border-radius: 0.5rem;
    border: solid 1px ${(props) => props.$border};
    background-color: ${(props) => props.$background};
    float: right;
    width: 20rem;
    min-height: 4rem;

    ${between(TABLET, SMALLDESKTOP)} {
        width: 15rem;
    }
`;

const Icon = styled.img`
    width: 1rem;
    height: 1rem;
    margin: auto;
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    margin: auto;
`;

interface IconDivProps {
    $background: string;
}
const IconDiv = styled.div<IconDivProps>`
    width: 1.5rem;
    height: 1.5rem;
    margin-left: 1rem;
    margin-top: 1rem;
    background-color: ${(props) => props.$background};
    border-radius: 1rem;
    position: relative;
`;

const CloseButton = styled(FontAwesomeIcon).attrs((props) => ({
    icon: faTimes,
}))`
    margin-left: auto;
    margin-right: 0.6em;
    margin-top: 0.6em;
    cursor: pointer;
`;

const ToastText = styled.p<{ $color: string }>`
    color: ${(props) => props.$color};
    width: 60%;
    font-size: 0.8rem;
    font-weight: 500;
    word-wrap: normal;
    margin-left: 1rem;
    margin-right: 0.75rem;
    margin-top: 0.85rem;
`;

const RightItem = styled.div`
    margin-left: auto;
`;

// export const ToastType = Object.freeze({ Success: 1, Warning: 2, Error: 3 });
export enum ToastType {
    SUCCESS,
    WARNING,
    ERROR,
}

interface ToastProps {
    onClose: () => void;
    type: ToastType;
}

const Toast = ({ onClose, children, type }: PropsWithChildren<ToastProps>) => {
    let primary: string;
    let secondary: string;
    let textcolor: string;
    let image: string;

    if (type === ToastType.SUCCESS) {
        primary = "#78d381";
        secondary = "#e9f8eb";
        textcolor = "#4ab255";
        image = "/svg/check.svg";
    } else if (type === ToastType.WARNING) {
        primary = "#fbcd4c";
        secondary = "#fcf5e1";
        textcolor = "#e8ad06";
        image = "/svg/bang.svg";
    } else {
        primary = "#e8746a";
        secondary = "#fbebe9";
        textcolor = "#e8746a";
        image = "/svg/x.svg";
    }

    return (
        <RightItem>
            <Rectangle $border={primary} $background={secondary}>
                <IconDiv $background={primary}>
                    <Icon src={image} />
                </IconDiv>
                <ToastText $color={textcolor}>{children}</ToastText>
                <CloseButton
                    // src="/svg/close.svg"
                    icon={faTimes} // TODO: we shouldn't need to do this
                    color={textcolor}
                    onClick={onClose}
                />
            </Rectangle>
        </RightItem>
    );
};

Toast.propTypes = {
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node
    ]),
    onClose: PropTypes.func,
    type: PropTypes.number,
};

export default Toast;
