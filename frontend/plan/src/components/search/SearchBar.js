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
    updateSearchText,
    updateRangeFilter
} from "../../actions";

function shouldSearch(filterData) {
    const searchString = filterData.searchString.length >= 3;
    let selectedReq = false;
    if (filterData.selectedReq) {
        for (const key of Object.keys(filterData.selectedReq)) {
            if (filterData.selectedReq[key] === 1) {
                selectedReq = true;
                break;
            }
        }
    }
    return searchString || selectedReq;
}

// eslint-disable-next-line no-shadow
function SearchBar({
    startSearch, loadRequirements, schoolReq, filterData, addSchoolReq,
    remSchoolReq, updateSearchText, updateRangeFilter 
}) {
    useEffect(() => {
        loadRequirements();
    }, [loadRequirements]);

    const conditionalStartSearch = (filterInfo) => {
        if (shouldSearch(filterInfo)) {
            startSearch(filterInfo);
        }
    };

    return (
        <nav className="bar level">
            <div className="level-left">
                <div className="level-item" id="searchdiv">
                    <SearchField
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        updateSearchText={updateSearchText}
                    />
                </div>

                <div className="level-item" id="filterdiv">
                    <span className="icon">
                        <i className="fas fa-filter" />
                    </span>
                    <p> Filter by</p>
                    <DropdownButton title="School Req">
                        <SchoolReq
                            startSearch={conditionalStartSearch}
                            schoolReq={schoolReq}
                            filterData={filterData}
                            addSchoolReq={addSchoolReq}
                            remSchoolReq={remSchoolReq}
                        />
                    </DropdownButton>
                    <DropdownButton title="Difficulty">
                        <RangeFilter
                            minRange={0}
                            maxRange={4}
                            step={0.01}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("difficulty")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="difficulty"
                        />
                    </DropdownButton>
                    <DropdownButton title="Course Quality">
                        <RangeFilter
                            minRange={0}
                            maxRange={4}
                            step={0.01}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("course_quality")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="course_quality"
                        />
                    </DropdownButton>
                    <DropdownButton title="Instructor Quality">
                        <RangeFilter
                            minRange={0}
                            maxRange={4}
                            step={0.01}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("instructor_quality")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="instructor_quality"
                        />
                    </DropdownButton>

                    <DropdownButton title="Time" />
                    <DropdownButton title="Type" />
                    <DropdownButton title="CU">
                        <RangeFilter
                            minRange={1}
                            maxRange={2}
                            step={0.5}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("cu")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="cu"
                        />
                    </DropdownButton>
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
        filterData: state.filters.filterData,
    }
);

const mapDispatchToProps = dispatch => ({
    loadRequirements: () => dispatch(loadRequirements()),
    startSearch: filterData => dispatch(fetchCourseSearch(filterData)),
    addSchoolReq: reqID => dispatch(addSchoolReq(reqID)),
    remSchoolReq: reqID => dispatch(remSchoolReq(reqID)),
    updateSearchText: s => dispatch(updateSearchText(s)),
    updateRangeFilter: field => values => dispatch(updateRangeFilter(field, values)),
});
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);
