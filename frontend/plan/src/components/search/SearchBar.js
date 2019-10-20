import React, { useEffect } from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";
import "./Search.css";
import { DropdownButton } from "../DropdownButton";
import { SchoolReq } from "./SchoolReq";
import { RangeFilter } from "./RangeFilter";
import { SearchField } from "./SearchField";
import { initialState as defaultFilters } from "../../reducers/filters";
import {
    fetchCourseSearch,
    loadRequirements,
    addSchoolReq,
    remSchoolReq,
    updateSearchText,
    updateRangeFilter,
    clearAll,
    clearFilter,
    updateSearch
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


function SearchBar({
    // eslint-disable-next-line no-shadow
    startSearch, loadRequirements, schoolReq, filterData, addSchoolReq,
    // eslint-disable-next-line no-shadow
    remSchoolReq, updateSearchText, updateRangeFilter, clearAll, clearFilter,
    // eslint-disable-next-line no-shadow
    defaultReqs, clearSearchResults,
}) {
    useEffect(() => {
        loadRequirements();
    }, [loadRequirements]);

    const conditionalStartSearch = (filterInfo) => {
        if (shouldSearch(filterInfo)) {
            startSearch(filterInfo);
        } else {
            clearSearchResults();
        }
    };

    const clearFilterSearch = property => () => {
        clearFilter(property);
        if (property === "selectedReq") {
            conditionalStartSearch({
                ...filterData,
                selectedReq: defaultReqs,
            });
        } else {
            conditionalStartSearch({
                ...filterData,
                [property]: defaultFilters.filterData[property],
            });
        }
    };

    return (
        <div className="bar level" style={{}}>
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
                    <DropdownButton title="School Req" filterData={filterData.selectedReq} defaultFilter={defaultReqs} clearFilter={clearFilterSearch("selectedReq")}>
                        <SchoolReq
                            startSearch={conditionalStartSearch}
                            schoolReq={schoolReq}
                            filterData={filterData}
                            addSchoolReq={addSchoolReq}
                            remSchoolReq={remSchoolReq}
                        />
                    </DropdownButton>
                    <DropdownButton title="Difficulty" filterData={filterData.difficulty} defaultFilter={defaultFilters.filterData.difficulty} clearFilter={clearFilterSearch("difficulty")}>
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
                    <DropdownButton title="Course Quality" filterData={filterData.course_quality} defaultFilter={defaultFilters.filterData.course_quality} clearFilter={clearFilterSearch("course_quality")}>
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
                    <DropdownButton title="Instructor Quality" filterData={filterData.instructor_quality} defaultFilter={defaultFilters.filterData.instructor_quality} clearFilter={clearFilterSearch("instructor_quality")}>
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

                    {/* <DropdownButton title="Time" />
                    <DropdownButton title="Type" /> */}
                    <DropdownButton title="CU" filterData={filterData.cu} defaultFilter={defaultFilters.filterData.cu} clearFilter={clearFilterSearch("cu")}>
                        <RangeFilter
                            minRange={0.5}
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
                    <button
                        className="button is-white"
                        type="button"
                        onClick={() => {
                            conditionalStartSearch({
                                ...defaultFilters.filterData,
                                searchString: filterData.searchString,
                                selectedReq: defaultReqs,
                            });
                            clearAll();
                        }}
                    >
                        Clear all
                    </button>
                </div>
            </div>
        </div>
    );
}

SearchBar.propTypes = {
    startSearch: PropTypes.func,
    loadRequirements: PropTypes.func,
    schoolReq: PropTypes.objectOf(PropTypes.array),
    addSchoolReq: PropTypes.func,
    remSchoolReq: PropTypes.func,
    updateSearchText: PropTypes.func,
    updateRangeFilter: PropTypes.func,
    clearAll: PropTypes.func,
    clearFilter: PropTypes.func,
    clearSearchResults: PropTypes.func,
    // eslint-disable-next-line react/forbid-prop-types
    filterData: PropTypes.object,
    defaultReqs: PropTypes.objectOf(PropTypes.number),
};

const mapStateToProps = state => (
    {
        schoolReq: state.filters.schoolReq,
        filterData: state.filters.filterData,
        defaultReqs: state.filters.defaultReqs,
    }
);

const mapDispatchToProps = dispatch => ({
    loadRequirements: () => dispatch(loadRequirements()),
    startSearch: filterData => dispatch(fetchCourseSearch(filterData)),
    addSchoolReq: reqID => dispatch(addSchoolReq(reqID)),
    remSchoolReq: reqID => dispatch(remSchoolReq(reqID)),
    updateSearchText: s => dispatch(updateSearchText(s)),
    updateRangeFilter: field => values => dispatch(updateRangeFilter(field, values)),
    clearAll: () => dispatch(clearAll()),
    clearFilter: propertyName => dispatch(clearFilter(propertyName)),
    clearSearchResults: () => dispatch(updateSearch([])),
});
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);
