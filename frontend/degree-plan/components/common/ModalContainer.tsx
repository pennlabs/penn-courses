// TODO: this is copied from plan, we should factor out into a shared component


import React, { PropsWithChildren, useRef } from "react";
import styled from "@emotion/styled";

interface ModalContainerProps {
    title: string;
    close: () => void;
    modalProps?: any;
    modalKey: string | null;
    isBig?: boolean;
}

const OuterModalContainer = styled.div<{ $title: string }>`
    align-items: center;
    display: ${(props) => (props.$title ? "flex " : "none ")} !important;
    flex-direction: column;
    justify-content: center;
    overflow: hidden;
    position: fixed;
    z-index: 1001; /* Above everything else*/
    bottom: 0;
    left: 0;
    right: 0;
    top: 0;
    header,
    footer {
        background-color: white;
    }

    .error_message {
        color: #e25455;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        min-height: 0.85rem;
    }
`;

const ModalBackground = styled.div`
    background-color: #707070;
    opacity: 0.75;
    bottom: 0;
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
`;

const ModalCard = styled.div<{ $isBig: boolean }>`
    border-radius: 4px;
    max-width: ${(props) => (props.$isBig ? "400px" : "1000px")} !important;
    max-height: ${(props) => (props.$isBig ? "275px" : "800px")} !important;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;

    @media (min-width: 769px) {
        margin: 0 auto;
        width: 400px;
    }

    input {
        border: 1px solid #d6d6d6 !important;
        border-radius: 0.3rem;
        padding: 0.35rem;
        width: 100%;
        margin-top: 0 !important;
        border: none;
        outline: none;
        transition: 200ms ease;
    }

    button {
        float: right;
    }

    button.is-link {
        background: #7876f3;
        font-weight: 600;
    }

    button.is-link:hover {
        background: #6e76cd;
    }

    button.is-link:active {
        background: #5d64ad;
    }
`;

const ModalCardHead = styled.header`
    display: flex;
    flex-direction: row;
    padding: 1.2rem 1.5rem 1rem;
    border-radius: 4px 4px 0 0;
    justify-content: space-between;
`;

const ModalCardTitle = styled.div`
    color: var(--modal-title-color);
    font-weight: 480;
    font-size: 1.1rem;
    line-height: 1;
`;

const ModalCardBody = styled.section`
    background-color: white;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    flex-shrink: 1;
    overflow: auto;
    padding: 0rem 1.5rem 1.5rem;
    .button,
    input {
        display: block;
        margin: 1.5rem auto auto;
    }
`;

/**
 * A generic container for modals
 * */
const ModalContainer = ({
    children,
    title,
    close,
    modalKey,
    modalProps = {},
    isBig = false,
}: PropsWithChildren<ModalContainerProps>) => {
    const modalRef = useRef(null);
    return (
        <OuterModalContainer $title={title} ref={modalRef}>
            <ModalBackground />
            <ModalCard $isBig={isBig}>
                <ModalCardHead>
                    <ModalCardTitle>{title}</ModalCardTitle>
                    <div
                        role="button"
                        aria-label="close"
                        onClick={close}
                        style={{ cursor: "pointer" }}
                    >
                        <span className="icon is-small">
                            <i className="fa fa-times" />
                        </span>
                    </div>
                </ModalCardHead>
                <ModalCardBody>
                    {modalKey && 
                        React.Children.map(children, (child: React.ReactNode) =>
                            React.cloneElement(child as React.ReactElement, {
                                close,
                                modalKey,
                                modalRef,
                                ...modalProps
                            })
                        )}
                </ModalCardBody>
            </ModalCard>
        </OuterModalContainer>
    )
};

export default ModalContainer;