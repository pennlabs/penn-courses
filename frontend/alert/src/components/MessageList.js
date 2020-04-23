import React from "react";
import PropTypes from "prop-types";
import styled from "styled-components";

import Toast, { ToastType } from "./Toast";
import { minWidth, TABLET } from "../constants";

const ToastContainer = styled.div`
display: flex;
flex-direction: column;

div {
margin-bottom: .25rem;
}
${minWidth(TABLET)} {
position: absolute;
right: 0;
margin-top: 1rem;
margin-right: 2rem;
}
`;

const MessageToast = ({ message, status, onClose }) => {
    let type;
    switch (status) {
        case 201:
            type = ToastType.Success;
            break;
        case 503:
            type = ToastType.Error;
            break;
        case 400: // no section
            type = ToastType.Warning;
            break;
        case 409: // duplicate
            type = ToastType.Warning;
            break;
        case 404:
            type = ToastType.Error;
            break;
        case 406:
            type = ToastType.Warning;
            break;
        case 500:
            type = ToastType.Error;
            break;
        default:
            type = ToastType.Warning;
    }
    return (
        <Toast
            type={type}
            onClose={onClose}
        >
            {message}
        </Toast>
    );
};

MessageToast.propTypes = {
    message: PropTypes.string,
    status: PropTypes.number,
    onClose: PropTypes.func,
};

const MessageList = ({ messages, removeMessage }) => (
    <ToastContainer>
        {messages.map(
            ({ message, status, key }) => (
                <MessageToast
                    key={key}
                    status={status}
                    message={message}
                    onClose={() => removeMessage(key)}
                />
            )
        )}
    </ToastContainer>
);

MessageList.propTypes = {
    messages: PropTypes.arrayOf(PropTypes.object),
    removeMessage: PropTypes.func,
};

export default MessageList;
