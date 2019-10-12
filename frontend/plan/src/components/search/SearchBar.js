import React, { useEffect } from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import "./Search.css";
import { DropdownButton } from "../DropdownButton";
import { SchoolReq } from "./SchoolReq";
import { RangeFilter } from "./RangeFilter";
import { SearchField } from "./SearchField";
import {
    fetchCourseSearch,
    loadRequirements,
    addSchoolReq,
    remSchoolReq,
} from "../../actions";

// eslint-disable-next-line no-shadow
function SearchBar({ startSearch, loadRequirements, schoolReq, filterSearch, addSchoolReq, remSchoolReq }) {
    useEffect(() => {
        loadRequirements();
    }, [loadRequirements]);
    return (
        <nav className="bar level">
            <div className="level-left">
                <div className="level-item" id="searchdiv">
                    <SearchField startSearch={startSearch(filterSearch)} />
                </div>

                <div className="level-item" id="filterdiv">
                    <span className="icon">
                        <i className="fas fa-filter" />
                    </span>
                    <p> Filter by</p>
                    <DropdownButton title="School Req">
                        <SchoolReq
                            schoolReq={schoolReq}
                            filterInfo={filterSearch.selectedReq}
                            addSchoolReq={addSchoolReq}
                            remSchoolReq={remSchoolReq}
                        />
                    </DropdownButton>
                    <DropdownButton title="Difficulty">
                        <RangeFilter filterInfo={filterSearch.difficulty} />
                    </DropdownButton>
                    <DropdownButton title="Quality">
                        <RangeFilter filterInfo={filterSearch.quality} />
                    </DropdownButton>
                    <DropdownButton title="Time" />
                    <DropdownButton title="Type" />
                    <DropdownButton title="CU" />
                </div>
            </div>
            <div className="level-right">
                <div className="level-item">
                    <button className="button is-white" type="button">
                        Clear all
                    </button>
                </div>
            </div>
        </nav>
    );
}

const mapStateToProps = state => (
    {
        schoolReq: state.filters.schoolReq,
        filterSearch: state.filters.filterSearch,
    }
);

const mapDispatchToProps = dispatch => ({
    loadRequirements: () => dispatch(loadRequirements()),
    startSearch: filterSearch => searchObj => dispatch(fetchCourseSearch(searchObj, filterSearch)),
    addSchoolReq: reqID => dispatch(addSchoolReq(reqID)),
    remSchoolReq: reqID => dispatch(remSchoolReq(reqID)),
});
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);
