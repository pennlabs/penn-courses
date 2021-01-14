import React, { PropsWithChildren } from "react";
import PropTypes from "prop-types";
import { connect, DispatchProp } from "react-redux";
import { closeModal } from "../../actions";
import {
    generateModalInterior,
    generateModalActions,
} from "./model_content_generator";
import { ThunkDispatch } from "redux-thunk";

interface ModalContainerProps {
    title: string;
    close: () => void;
    modalProps: any;
    modalKey: string;
    isBig: boolean;
}

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
    isBig,
}: PropsWithChildren<ModalContainerProps> & DispatchProp) => (
    <div className={`modal ${title ? "is-active" : ""}`}>
        <div className="modal-background" />
        <div className={`modal-card ${isBig ? " big" : ""}`}>
            <header className="modal-card-head">
                <header className="modal-card-title">{title}</header>
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
            </header>
            <section className="modal-card-body">
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
            </section>
        </div>
    </div>
);

const bigModals = { WELCOME: true };

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
