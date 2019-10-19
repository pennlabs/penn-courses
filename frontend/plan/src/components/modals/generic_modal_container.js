import React from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import { closeModal } from "../../actions";
import { generateModalInterior, generateModalActions } from "./model_content_generator";

/**
 * A generic container for modals
 * */
const ModalContainer = ({
    children, title, close, dispatch, modalKey, modalProps,
}) => (
    <div className={`modal ${title ? "is-active" : ""}`}>
        <div className="modal-background" />
        <div className="modal-card">
            <header className="modal-card-head">
                <header className="modal-card-title">{title}</header>
                <div
                    role="button"
                    aria-label="close"
                    onClick={close}
                    style={{ cursor: "pointer" }}
                >
                    <span className="icon is-small">
                        <i className="fa fa-times" style={{ color: "rgba(0, 0, 0, 0.2)" }} />
                    </span>
                </div>
            </header>
            <section className="modal-card-body">
                {modalKey && React.Children.map(children, child => React.cloneElement(child, {
                    close,
                    ...modalProps,
                    ...generateModalActions(dispatch, modalKey, modalProps),
                }))}
            </section>
        </div>
    </div>
);

ModalContainer.propTypes = {
    title: PropTypes.string.isRequired,
    close: PropTypes.func.isRequired,
    dispatch: PropTypes.func.isRequired,
    modalProps: PropTypes.objectOf(PropTypes.any),
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node
    ]),
    modalKey: PropTypes.string,
};

const mapStateToProps = state => ({
    children: generateModalInterior(state),
    title: state.modals.modalTitle,
    modalKey: state.modals.modalKey,
    modalProps: state.modals.modalProps,
});

const mapDispatchToProps = dispatch => ({
    close: () => dispatch(closeModal()),
    dispatch,
});

export default connect(mapStateToProps, mapDispatchToProps)(ModalContainer);
