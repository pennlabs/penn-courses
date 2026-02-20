import React from "react";
import PropTypes from "prop-types";
import styled from "styled-components";

import Toast, { ToastType } from "./Toast";
import { minWidth, TABLET } from "../constants";

const ToastContainer = styled.div`
    display: flex;
    flex-direction: column;

    div {
        margin-bottom: 0.25rem;
    }
    ${minWidth(TABLET)} {
        position: absolute;
        right: 0;
        margin-top: 1rem;
        margin-right: 2rem;
    }
`;

interface MessageToastProps {
    message: string;
    status: number;
    onClose: () => void;
}
const MessageToast = ({ message, status, onClose }: MessageToastProps) => {
    let type;
    switch (status) {
        case 201:
            type = ToastType.SUCCESS;
            break;
        case 503:
            type = ToastType.ERROR;
            break;
        case 400: // no section
            type = ToastType.WARNING;
            break;
        case 409: // duplicate
            type = ToastType.WARNING;
            break;
        case 404:
            type = ToastType.ERROR;
            break;
        case 406:
            type = ToastType.WARNING;
            break;
        case 500:
            type = ToastType.ERROR;
            break;
        default:
            type = ToastType.WARNING;
    }
    return (
        <Toast type={type} onClose={onClose}>
            {message}
        </Toast>
    );
};

interface MessageList {
    messages: {
        message: string;
        status: number;
        key: number;
    }[];
    removeMessage: (key: number) => void;
}
const MessageList = ({ messages, removeMessage }) => (
    <ToastContainer>
        {messages.map(({ message, status, key }) => (
            <MessageToast
                key={key}
                status={status}
                message={message}
                onClose={() => removeMessage(key)}
            />
        ))}
    </ToastContainer>
);

export default MessageList;
