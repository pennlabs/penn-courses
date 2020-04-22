import React from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";
import x from "../assets/x.svg";
import close from "../assets/close.svg";
import bang from "../assets/bang.svg";
import check from "../assets/check.svg";

const Rectangle = styled.div`
    display: flex;
    flex-direction: row;
    border-radius: 0.5rem;
    border: solid 1px ${props => props.border};
    background-color: ${props => props.background};
    float: right;
    width: 20rem;
    height: 4rem;
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

const IconDiv = styled.div`
    width: 1.5rem;
    height: 1.5rem;
    margin-left: 1rem;
    margin-top: 1rem;
    background-color: ${props => props.background};
    border-radius: 1rem;
    position: relative;
`;

const CloseButton = styled(FontAwesomeIcon).attrs(props => ({ icon: faTimes }))`
    margin-left:auto;
    margin-right: 0.6em;
    margin-top: 0.6em;
    cursor: pointer;
`;


const ToastText = styled.p`
    color: ${props => props.color};
    max-width: 70%;
    font-size: 0.8rem;
    font-weight: 500;
    word-wrap: normal;
    margin-left: 1rem;
    margin-right: 0.75rem;
    margin-top: .85rem;
`;

const RightItem = styled.div`
    margin-left: auto;
`;

export const ToastType = Object.freeze({ Success: 1, Warning: 2, Error: 3 });

const Toast = ({
    onClose, children, isSuccess, isWarning, isError, type,
}) => {
    let primary;
    let secondary;
    let textcolor;
    let image;

    if (isSuccess || type === ToastType.Success) {
        primary = "#78d381";
        secondary = "#e9f8eb";
        textcolor = "#4ab255";
        image = check;
    } else if (isWarning || type === ToastType.Warning) {
        primary = "#fbcd4c";
        secondary = "#fcf5e1";
        textcolor = "#e8ad06";
        image = bang;
    } else if (isError || type === ToastType.Error) {
        primary = "#e8746a";
        secondary = "#fbebe9";
        textcolor = "#e8746a";
        image = x;
    }

    return (
        <RightItem>
            <Rectangle border={primary} background={secondary}>
                <IconDiv background={primary}>
                    <Icon src={image} />
                </IconDiv>
                <ToastText color={textcolor}>
                    {children}
                </ToastText>
                <CloseButton src={close} color={textcolor} onClick={onClose} />
            </Rectangle>
        </RightItem>
    );
};

Toast.propTypes = {
    isSuccess: PropTypes.any, // eslint-disable-line
    isWarning: PropTypes.any, // eslint-disable-line
    isError: PropTypes.any,   // eslint-disable-line
    children: PropTypes.arrayOf(PropTypes.element),
    onClose: PropTypes.func,
    type: PropTypes.number,
};

export default Toast;
