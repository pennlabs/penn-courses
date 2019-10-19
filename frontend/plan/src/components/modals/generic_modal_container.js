import React from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import { closeModal } from "../../actions";

/**
 * A generic container for modals
 * */
const ModalContainer = ({
    children, title, close, modalActions,
}) => (
    <div className={`modal ${children ? "is-active" : ""}`}>
        <div className="modal-background" />
        <div className="modal-card">
            <header className="modal-card-head">
                <p className="modal-card-title">{title}</p>
                <button className="delete" aria-label="close" onClick={close} type="button" />
            </header>
            <section className="modal-card-body">
                {React.children.map(children, child => React.cloneElement(child, { modalActions }))}
            </section>
        </div>
    </div>
);

ModalContainer.propTypes = {
    title: PropTypes.string.isRequired,
    close: PropTypes.func.isRequired,
    modalActions: PropTypes.shape({ }),
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.node),
        PropTypes.node
    ]),
};

const generateModalInterior = reduxState => null;
// TODO
// Case on state to generate a modal component
// The modal component should access props.modalAction

const mapStateToProps = state => ({
    children: generateModalInterior(state),
});

const mapDispatchToProps = dispatch => ({
    close: () => dispatch(closeModal()),
    modalActions: {},
});

export default connect(mapStateToProps, mapDispatchToProps)(ModalContainer);
