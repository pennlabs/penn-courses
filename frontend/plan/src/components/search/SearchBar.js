import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { isMobileOnly } from "react-device-detect";
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
    defaultReqs, clearSearchResults, isLoadingCourseInfo, isSearchingCourseInfo,
    setTab,
}) {
    useEffect(() => {
        loadRequirements();
    }, [loadRequirements]);

    const [reqsShown, showHideReqs] = useState(false);

    const conditionalStartSearch = (filterInfo) => {
        if (shouldSearch(filterInfo)) {
            startSearch(filterInfo);
        } else {
            clearSearchResults();
        }
    };

    const isLoading = isLoadingCourseInfo || isSearchingCourseInfo;

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

    if (isMobileOnly) {
        return (
            <div style={{ marginTop: "0px" }}>
                <div style={{
                    display: "flex", justifyContent: "center", alignItems: "center", flexWrap: "wrap", background: "white", paddingTop: "20px", paddingBottom: "10px", marginBottom: "10px", borderRadius: "6px",
                }}
                >
                    <div>
                        <img src="/static/favicon.ico" alt="" style={{ height: "2.5rem", padding: "0 1rem" }} />
                    </div>
                    <SearchField
                        setTab={setTab}
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        updateSearchText={updateSearchText}
                        isDisabled={isLoading}
                    />
                    <div style={{ paddingLeft: "10px" }} role="button" onClick={() => showHideReqs(!reqsShown)}>
                        <i className="fas fa-filter" />
                    </div>
                </div>
                {reqsShown && (
                    <div style={{
                        zIndex: "100", marginTop: "-20px", padding: "10px", marginBottom: "20px", display: "flex", width: "100vw", alignItems: "center", flexWrap: "wrap", background: "white", justifyContent: "flex-start",
                    }}
                    >
                        <DropdownButton title="Requirements" filterData={filterData.selectedReq} defaultFilter={defaultReqs} clearFilter={clearFilterSearch("selectedReq")} isDisabled={isLoading}>
                            <SchoolReq
                                startSearch={conditionalStartSearch}
                                schoolReq={schoolReq}
                                filterData={filterData}
                                addSchoolReq={addSchoolReq}
                                remSchoolReq={remSchoolReq}
                                isDisabled={isLoading}
                            />
                        </DropdownButton>
                        <DropdownButton title="Difficulty" filterData={filterData.difficulty} defaultFilter={defaultFilters.filterData.difficulty} clearFilter={clearFilterSearch("difficulty")} isDisabled={isLoading}>
                            <RangeFilter
                                minRange={0}
                                maxRange={4}
                                step={0.25}
                                filterData={filterData}
                                updateRangeFilter={updateRangeFilter("difficulty")}
                                startSearch={conditionalStartSearch}
                                rangeProperty="difficulty"
                                isDisabled={isLoading}
                            />
                        </DropdownButton>
                        <DropdownButton title="Course Quality" filterData={filterData.course_quality} defaultFilter={defaultFilters.filterData.course_quality} clearFilter={clearFilterSearch("course_quality")} isDisabled={isLoading}>
                            <RangeFilter
                                minRange={0}
                                maxRange={4}
                                step={0.25}
                                filterData={filterData}
                                updateRangeFilter={updateRangeFilter("course_quality")}
                                startSearch={conditionalStartSearch}
                                rangeProperty="course_quality"
                                isDisabled={isLoading}
                            />
                        </DropdownButton>
                        <DropdownButton title="Instructor Quality" filterData={filterData.instructor_quality} defaultFilter={defaultFilters.filterData.instructor_quality} clearFilter={clearFilterSearch("instructor_quality")} isDisabled={isLoading}>
                            <RangeFilter
                                minRange={0}
                                maxRange={4}
                                step={0.25}
                                filterData={filterData}
                                updateRangeFilter={updateRangeFilter("instructor_quality")}
                                startSearch={conditionalStartSearch}
                                rangeProperty="instructor_quality"
                                isDisabled={isLoading}
                            />
                        </DropdownButton>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="bar level is-mobile" style={{ height: "auto" }}>
            <div className="level-left" style={{ maxWidth: "80vw" }}>
                <div className="level-item">
                    <img src="/static/favicon.ico" alt="" style={{ height: "2rem", paddingLeft: "1.5rem" }} />
                </div>
                <div className="level-item" id="searchdiv">
                    <SearchField
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        updateSearchText={updateSearchText}
                        isDisabled={isLoading}
                    />
                </div>

                <div className="level-item filterContainer" id="filterdiv">
                    <span className="icon">
                        <i className="fas fa-filter" />
                    </span>
                    <p> Filter by</p>
                    <DropdownButton title="Requirements" filterData={filterData.selectedReq} defaultFilter={defaultReqs} clearFilter={clearFilterSearch("selectedReq")} isDisabled={isLoading}>
                        <SchoolReq
                            startSearch={conditionalStartSearch}
                            schoolReq={schoolReq}
                            filterData={filterData}
                            addSchoolReq={addSchoolReq}
                            remSchoolReq={remSchoolReq}
                            isDisabled={isLoading}
                        />
                    </DropdownButton>
                    <DropdownButton title="Difficulty" filterData={filterData.difficulty} defaultFilter={defaultFilters.filterData.difficulty} clearFilter={clearFilterSearch("difficulty")} isDisabled={isLoading}>
                        <RangeFilter
                            minRange={0}
                            maxRange={4}
                            step={0.25}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("difficulty")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="difficulty"
                            isDisabled={isLoading}
                        />
                    </DropdownButton>
                    <DropdownButton title="Course Quality" filterData={filterData.course_quality} defaultFilter={defaultFilters.filterData.course_quality} clearFilter={clearFilterSearch("course_quality")} isDisabled={isLoading}>
                        <RangeFilter
                            minRange={0}
                            maxRange={4}
                            step={0.25}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("course_quality")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="course_quality"
                            isDisabled={isLoading}
                        />
                    </DropdownButton>
                    <DropdownButton title="Instructor Quality" filterData={filterData.instructor_quality} defaultFilter={defaultFilters.filterData.instructor_quality} clearFilter={clearFilterSearch("instructor_quality")} isDisabled={isLoading}>
                        <RangeFilter
                            minRange={0}
                            maxRange={4}
                            step={0.25}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("instructor_quality")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="instructor_quality"
                            isDisabled={isLoading}
                        />
                    </DropdownButton>

                    {/* <DropdownButton title="Time" />
                    <DropdownButton title="Type" /> */}
                    {/* <DropdownButton title="CU" filterData={filterData.cu}
                    defaultFilter={defaultFilters.filterData.cu}
                    clearFilter={clearFilterSearch("cu")} isDisabled={isLoading}>
                        <RangeFilter
                            minRange={0.5}
                            maxRange={2}
                            step={0.5}
                            filterData={filterData}
                            updateRangeFilter={updateRangeFilter("cu")}
                            startSearch={conditionalStartSearch}
                            rangeProperty="cu"
                            isDisabled={isLoading}
                        />
                    </DropdownButton> */}
                </div>
            </div>
            <div className="level-right is-hidden-mobile">
                <div className="level-item">
                    <button
                        className="button is-white"
                        style={{ marginRight: "1em", color: "#7e7e7e" }}
                        type="button"
                        onClick={() => {
                            conditionalStartSearch({
                                ...defaultFilters.filterData,
                                searchString: filterData.searchString,
                                selectedReq: defaultReqs,
                            });
                            clearAll();
                        }}
                        disabled={isLoading ? "disabled" : false}
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
    isLoadingCourseInfo: PropTypes.bool,
    isSearchingCourseInfo: PropTypes.bool,
    setTab: PropTypes.func,
};

const mapStateToProps = state => (
    {
        schoolReq: state.filters.schoolReq,
        filterData: state.filters.filterData,
        defaultReqs: state.filters.defaultReqs,
        isLoadingCourseInfo: state.sections.courseInfoLoading,
        isSearchingCourseInfo: state.sections.searchInfoLoading,
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
