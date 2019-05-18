import React, { Component } from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import { Dropdown } from "../dropdown";
import SummaryDropdown from "./summary";
import {
    changeSchedule, fetchCourseSearch, openModal, toggleSearchFilterShown
} from "../../actions";
import { NEW_SCHEDULE_MODAL_NAME } from "../modals/new_schedule_modal";
import SchedulesDropdown from "./SchedulesDropdown";
import { DELETE_SCHEDULE_MODAL_NAME } from "../modals/delete_schedule_modal";
import { RENAME_SCHEDULE_MODAL_NAME } from "../modals/rename_schedule_modal_container";
import { DUPLICATE_SCHEDULE_MODAL_NAME } from "../modals/duplicate_schedule_modal_container";
import { CLEAR_SCHEDULE_MODAL_NAME } from "../modals/clear_schedule_modal";

class SearchBar extends Component {
    constructor(props) {
        super(props);
        this.state = { searchFilterOpened: false };
    }

    handleSubmit = (event) => {
        const {
            startSearch,
        } = this.props;
        event.preventDefault();
        startSearch({ searchType: "courseIDSearch", param: event.target.getElementsByTagName("input")[0].value });
    }

    searchToggler = () => {
        const {
            searchFilterOpened,
        } = this.state;

        const {
            // eslint-disable-next-line no-shadow
            toggleSearchFilterShown,
        } = this.props;
        const selectedBackground = searchFilterOpened ? "images/filter_b.png" : "images/filter_a.png";
        let node;
        return (
            <div
                id="filter_search_toggler"
                ref={(c) => { node = c; }}
                onClick={() => {
                    this.setState({ searchFilterOpened: !searchFilterOpened });
                    toggleSearchFilterShown(node.getBoundingClientRect());
                }}
                style={{ backgroundImage: `url(${selectedBackground})` }}
                role="button"
            />
        );
    }

    render() {
        /* eslint-disable no-shadow */
        const {
            showNewScheduleModal,
            showDuplicateScheduleModal,
            showRenameScheduleModal,
            showClearScheduleModal,
            showDeleteScheduleModal,
            scheduleNames,
            scheduleSelected,
            changeSchedule,
        } = this.props;
        /* eslint-enable no-shadow */
        return (
            <div id="searchbar" className="level">
                <span className="level-left">

                    <div id="searchSelectContainer">
                        <Dropdown
                            id="searchSelect"
                            updateLabel={true}
                            defActive={0}
                            defText="Search By"
                            contents={[
                                ["Course ID", () => {
                                }],
                                ["Keywords", () => {
                                }],
                                ["Instructor", () => {
                                }]
                            ]}
                        />
                    </div>

                    <form
                        onSubmit={this.handleSubmit}
                    >
                        <input
                            id="CSearch"
                            type="text"
                            className="input is-small is-rounded"
                            name="courseSearch"
                            autoComplete="off"
                            placeholder="Search for a department, course, or section"
                        />
                    </form>
                    {this.searchToggler()}
                </span>

                <span className="level-right">
                    <div id="scheduleOptionsContainer">
                        <Dropdown
                            id="scheduleDropdown"
                            defText="Schedule Options"
                            contents={[
                                ["New", () => {
                                    showNewScheduleModal();
                                }],
                                ["Download", () => {
                                }],
                                ["Duplicate", () => {
                                    showDuplicateScheduleModal();
                                }],
                                ["Rename", () => {
                                    showRenameScheduleModal();
                                }],
                                ["Clear", () => {
                                    showClearScheduleModal();
                                }],
                                ["Delete", () => {
                                    showDeleteScheduleModal();
                                }]
                            ]}
                        />
                    </div>
                    <button className="button" type="button">
                        <span>Show Stars</span>
                    </button>
                    <a className="button" href="#UploadModal" id="ImportButton">
                    Import
                    </a>
                    <button className="button" type="button">
                        <span>Clear Search</span>
                    </button>
                    <div className="dropdown">
                        <div className="dropdown-trigger">
                            <button className="button" aria-haspopup="true" aria-controls="dropdown-menu" type="button">
                                <span>
                                    <span className="selected_name">Schedules</span>
                                    <span className="icon is-small">
                                        <i className="fa fa-angle-down" />
                                    </span>
                                </span>
                            </button>
                        </div>
                    </div>

                    {/* Course summary dropdown */}
                    <SummaryDropdown />
                    <SchedulesDropdown
                        scheduleNames={scheduleNames}
                        scheduleSelected={scheduleSelected}
                        changeSchedule={changeSchedule}
                    />
                </span>
            </div>
        );
    }
}

const mapStateToProps = state => (
    {
        scheduleNames: Object.keys(state.schedule.schedules),
        scheduleSelected: state.schedule.scheduleSelected,
    }
);


const mapDispatchToProps = dispatch => ({
    toggleSearchFilterShown: rect => dispatch(toggleSearchFilterShown(rect)),
    showNewScheduleModal: () => dispatch(openModal(NEW_SCHEDULE_MODAL_NAME)),
    showDeleteScheduleModal: () => dispatch(openModal(DELETE_SCHEDULE_MODAL_NAME)),
    showRenameScheduleModal: () => dispatch(openModal(RENAME_SCHEDULE_MODAL_NAME)),
    showDuplicateScheduleModal: () => dispatch(openModal(DUPLICATE_SCHEDULE_MODAL_NAME)),
    changeSchedule: scheduleName => dispatch(changeSchedule(scheduleName)),
    showClearScheduleModal: () => dispatch(openModal(CLEAR_SCHEDULE_MODAL_NAME)),
    startSearch: searchObj => dispatch(fetchCourseSearch(searchObj)),
});
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);

SearchBar.propTypes = {
    startSearch: PropTypes.func.isRequired,
    toggleSearchFilterShown: PropTypes.func.isRequired,
    showNewScheduleModal: PropTypes.func.isRequired,
    showDeleteScheduleModal: PropTypes.func.isRequired,
    showRenameScheduleModal: PropTypes.func.isRequired,
    showDuplicateScheduleModal: PropTypes.func.isRequired,
    showClearScheduleModal: PropTypes.func.isRequired,
    scheduleNames: PropTypes.arrayOf(PropTypes.string),
    scheduleSelected: PropTypes.string,
    changeSchedule: PropTypes.func.isRequired,
};
