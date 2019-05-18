/* eslint-disable react/prop-types */
import React, { Component } from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import {
    clearSchedule,
    closeModal,
    createSchedule,
    deleteSchedule,
    duplicateSchedule,
    openModal,
    renameSchedule,
    triggerModalAction
} from "../../actions";

/**
 * A generic container for modals
 * Pass in one or more components as the containedContent prop that will be
 * displayed within the modal container
 * */
class ModalContainer extends Component {
    constructor(props) {
        super(props);
        this.state = {
            hasAction: true,
        };
    }


    render() {
        const {
            /* eslint-disable no-shadow */
            openModal,
            modalName,
            containedContent,
            existingScheduleNames,
            triggerModalAction,
            modalActionState,
            createNewSchedule,
            deleteSchedule,
            renameSchedule,
            duplicateSchedule,
            clearSchedule,
            close,
            title,
            successButton,
            /* eslint-enable no-shadow */
        } = this.props;

        const {
            hasAction,
        } = this.state;

        const isOpen = openModal != null && openModal === modalName;


        const newContainedContent = React.Children.map(containedContent, child => (
            // provides all necessary functionality to contents of modal
            React.cloneElement(child, {
                existingScheduleNames,
                triggerModalAction,
                modalActionState,
                createNewSchedule,
                deleteSchedule,
                renameSchedule,
                duplicateSchedule,
                clearSchedule,
                close,
                clearAction: () => (hasAction ? this.setState({ hasAction: false }) : null),
                restoreAction: () => (!hasAction ? this.setState({ hasAction: true }) : null),
            })
        ));
        return isOpen && (
            <div className={`modal ${isOpen ? "is-active" : ""}`}>
                <div className="modal-background" />
                <div className="modal-card">
                    <header className="modal-card-head">
                        <p className="modal-card-title">{title}</p>
                        <button className="delete" aria-label="close" onClick={close} type="button" />
                    </header>
                    <section className="modal-card-body">
                        {newContainedContent}
                    </section>
                    <footer className="modal-card-foot">

                        {hasAction && successButton && (
                            <button
                                className="button is-success"
                                onClick={() => {
                                    triggerModalAction("success");
                                }}
                                type="button"
                            >
                                {successButton}
                            </button>
                        )}
                        <button
                            className="button is-light"
                            onClick={close}
                            type="button"
                        >
                            {hasAction ? "Cancel" : "Ok"}
                        </button>
                    </footer>
                </div>
            </div>
        );
    }
}

ModalContainer.propTypes = {
    // The name of the modal this container is used for;
    // should be consistent with the name used in Redux state
    modalName: PropTypes.string,
    // The text contained within the success button.
    // There will be no success button if this is set to undefined.
    successButton: PropTypes.string,
    // The components to display within the modal.
    // Should be an array of components or an individual component
    // TODO: replace this with the more standard 'children' prop
    containedContent: undefined,
    // The following props are set through React-Redux and should not be set elsewhere
    openModal: PropTypes.string,
    triggerModalAction: PropTypes.func,
    close: PropTypes.func,
};

const mapStateToProps = state => ({
    openModal: state.modals.modalShown,
    existingScheduleNames: Object.keys(state.schedule.schedules),
    modalActionState: state.modals.modalAction,
});

const mapDispatchToProps = dispatch => ({
    close: () => dispatch(closeModal()),
    open: modalName => dispatch(openModal(modalName)),
    triggerModalAction: modalAction => dispatch(triggerModalAction(modalAction)),
    createNewSchedule: name => dispatch(createSchedule(name)),
    deleteSchedule: () => dispatch(deleteSchedule()),
    renameSchedule: name => dispatch(renameSchedule(name)),
    duplicateSchedule: name => dispatch(duplicateSchedule(name)),
    clearSchedule: () => dispatch(clearSchedule()),
});

export default connect(mapStateToProps, mapDispatchToProps)(ModalContainer);
