import React, { PropsWithChildren } from "react";
import styled from "styled-components";
import { connect, DispatchProp } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import { closeModal } from "../../actions";
import {
    generateModalInterior,
    generateModalActions,
} from "./model_content_generator";

interface ModalContainerProps {
    title: string;
    close: () => void;
    modalProps: any;
    modalKey: string;
    isBig: boolean;
}

const OuterModalContainer = styled.div<{ $title: string }>`
    align-items: center;
    display: ${(props) => (props.$title ? "flex " : "none ")} !important;
    flex-direction: column;
    justify-content: center;
    overflow: hidden;
    position: fixed;
    z-index: 2000 !important;
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
    max-width: ${(props) => (props.$isBig ? "1000px" : "700px")} !important;
    max-height: ${(props) => (props.$isBig ? "600px" : "400px")} !important;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;

    @media (min-width: 769px) {
        margin: 0 auto;
        width: ${(props) => (props.$isBig ? "600px" : "400px")}
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
    align-items: center;
    display: flex;
    flex-shrink: 0;
    justify-content: flex-start;
    padding: 20px;
    position: relative;
    border-bottom: none !important;
    background-color: white !important;
    font-weight: bold;
    border-radius: 4px !important;
    border-radius: 4px 4px 0 0 !important;
    padding-left: 2rem;
    padding-right: 2rem;
`;

const ModalCardTitle = styled.header`
    color: #363636;
    flex-grow: 1;
    flex-shrink: 0;
    font-size: 1.5rem;
    line-height: 1;
`;

const ModalCardBody = styled.section`
    background-color: white;
    flex-grow: 1;
    flex-shrink: 1;
    overflow: auto;
    padding-left: 2rem;
    padding-right: 2rem;
    padding-bottom: 1.5rem;
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
    dispatch,
    modalKey,
    modalProps,
    isBig: isBig,
}: PropsWithChildren<ModalContainerProps> & DispatchProp) => (
    <OuterModalContainer $title={title}>
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
                            ...modalProps,
                            ...generateModalActions(
                                dispatch,
                                modalKey,
                                modalProps
                            ),
                        })
                    )}
            </ModalCardBody>
        </ModalCard>
    </OuterModalContainer>
);

const bigModals = { WELCOME: true};

const mapStateToProps = (state: any) => ({
    children: generateModalInterior(state),
    title: state.modals.modalTitle,
    modalKey: state.modals.modalKey,
    modalProps: state.modals.modalProps,
    // @ts-ignore
    isBig: bigModals[state.modals.modalKey],
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    close: () => dispatch(closeModal()),
    dispatch,
});

export default connect(mapStateToProps, mapDispatchToProps)(ModalContainer);
