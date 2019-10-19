import React from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import { closeModal } from "../../actions";
import { generateModalInterior, generateModalActions } from "./model_content_generator";

/**
 * A generic container for modals
 * */
const ModalContainer = ({
    children, title, close, dispatch, modalKey, modalProps
}) => (
    <div className={`modal ${title ? "is-active" : ""}`}>
        <div className="modal-background"/>
        <div className="modal-card">
            <header className="modal-card-head">
                <p className="modal-card-title">{title}</p>
                <button className="delete" aria-label="close" onClick={close} type="button"/>
            </header>
            <section className="modal-card-body">
                {modalKey && React.children.map(children, child =>
                    React.cloneElement(child, {
                        ...modalProps,
                        ... generateModalActions(dispatch, modalKey, modalProps),
                    }))}
            </section>
        </div>
    </div>
);

ModalContainer.propTypes = {
    title: PropTypes.string.isRequired,
    close: PropTypes.func.isRequired,
    dispatch: PropTypes.func.isRequired,
    modalProps: PropTypes.object,
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node
    ]),
    modalKey: PropTypes.string,
};

const mapStateToProps = state => ({
    children: generateModalInterior(state),
    title: state.modals.modalTitle,
    key: state.modals.modalKey,
    modalProps: state.modals.modalProps,
});

const mapDispatchToProps = dispatch => ({
    close: () => dispatch(closeModal()),
    dispatch,
});

export default connect(mapStateToProps, mapDispatchToProps)(ModalContainer);
