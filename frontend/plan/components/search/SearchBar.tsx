import React, { useEffect, useState } from "react";
import { connect } from "react-redux";
// TODO: Move shared components to typescript
// @ts-ignore
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import { useRouter } from "next/router";
import { DropdownButton } from "../DropdownButton";
import { SchoolReq } from "./SchoolReq";
import { RangeFilter } from "./RangeFilter";
import { CheckboxFilter } from "./CheckboxFilter";
import { SearchField } from "./SearchField";
import { initialState as defaultFilters } from "../../reducers/filters";
import initiateSync from "../syncutils";
import { FilterData, User, Requirement } from "../../types";

import {
    fetchCourseSearch,
    loadRequirements,
    addSchoolReq,
    remSchoolReq,
    updateSearchText,
    updateRangeFilter,
    updateCheckboxFilter,
    clearAll,
    clearFilter,
    updateSearch,
    clearAllScheduleData,
} from "../../actions";
import { login, logout } from "../../actions/login";

// removed: <F, K extends keyof F, V extends keyof K>
interface SearchBarProps {
    startSearch: (searchObj: FilterData) => void;
    loadRequirements: () => void;
    schoolReq: {
        SEAS: Requirement[];
        WH: Requirement[];
        SAS: Requirement[];
        NURS: Requirement[];
    };
    filterData: FilterData;
    addSchoolReq: (school: string) => void;
    remSchoolReq: (school: string) => void;
    updateSearchText: (text: string) => void;
    updateRangeFilter: (field: string) => (values: [number, number]) => void;
    clearAll: () => void;
    clearFilter: (search: string) => void;
    defaultReqs: { [x: string]: boolean };
    clearSearchResults: () => void;
    isLoadingCourseInfo: boolean;
    isSearchingCourseInfo: boolean;
    updateCheckboxFilter: (
        field: string,
        value: string,
        toggleState: boolean
    ) => void;
    setTab: (tab: number) => void;
    setView: (view: number) => void;
    user: User;
    login: (u: User) => void;
    logout: () => void;
    mobileView: boolean;
    isExpanded: boolean;
    clearScheduleData: () => void;
    store: object;
    storeLoaded: boolean;
}

function shouldSearch(filterData: FilterData) {
    const searchString = filterData.searchString.length >= 3;
    let selectedReq = false;
    if (filterData.selectedReq) {
        for (const key of Object.keys(filterData.selectedReq)) {
            if (filterData.selectedReq[key]) {
                selectedReq = true;
                break;
            }
        }
    }
    return searchString || selectedReq;
}

function SearchBar({
    /* eslint-disable no-shadow */
    startSearch, // from redux - dispatches fetch course search function (actions/index.js)
    loadRequirements,
    schoolReq,
    filterData,
    addSchoolReq,
    remSchoolReq,
    updateSearchText,
    updateRangeFilter,
    clearAll,
    clearFilter,
    defaultReqs,
    clearSearchResults,
    isLoadingCourseInfo,
    isSearchingCourseInfo,
    updateCheckboxFilter,
    setTab,
    setView,
    user,
    login,
    logout,
    mobileView,
    isExpanded,
    clearScheduleData,
    store,
    storeLoaded,
}: /* eslint-enable no-shadow */
SearchBarProps) {
    const router = useRouter();

    useEffect(() => {
        loadRequirements();
    }, [loadRequirements]);

    useEffect(() => {
        // ensure that the user is logged in before initiating the sync
        if (user && storeLoaded) {
            initiateSync(store);
        }
    }, [user, store, storeLoaded]);

    const [reqsShown, showHideReqs] = useState(false);

    const conditionalStartSearch = (filterInfo: FilterData) => {
        if (shouldSearch(filterInfo)) {
            startSearch(filterInfo);
        }
    };

    const clearFilterSearch = <V extends keyof FilterData>(
        property: V
    ) => () => {
        clearFilter(property);
        // filterData["selectedReq"] = defaultReqs;
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
    const dropDowns = (
        <>
            <DropdownButton
                title="Requirements"
                filterData={filterData.selectedReq}
                defaultFilter={defaultReqs}
                clearFilter={clearFilterSearch("selectedReq")}
            >
                <SchoolReq
                    startSearch={conditionalStartSearch}
                    schoolReq={schoolReq}
                    filterData={filterData}
                    addSchoolReq={addSchoolReq}
                    remSchoolReq={remSchoolReq}
                />
            </DropdownButton>
            <DropdownButton
                title="Difficulty"
                filterData={filterData.difficulty}
                defaultFilter={defaultFilters.filterData.difficulty}
                clearFilter={clearFilterSearch("difficulty")}
            >
                <RangeFilter
                    minRange={0}
                    maxRange={4}
                    step={0.25}
                    filterData={filterData}
                    updateRangeFilter={updateRangeFilter("difficulty")}
                    startSearch={conditionalStartSearch}
                    rangeProperty="difficulty"
                />
            </DropdownButton>
            <DropdownButton
                title="Course Quality"
                filterData={filterData.course_quality}
                defaultFilter={defaultFilters.filterData.course_quality}
                clearFilter={clearFilterSearch("course_quality")}
            >
                <RangeFilter
                    minRange={0}
                    maxRange={4}
                    step={0.25}
                    filterData={filterData}
                    updateRangeFilter={updateRangeFilter("course_quality")}
                    startSearch={conditionalStartSearch}
                    rangeProperty="course_quality"
                />
            </DropdownButton>
            <DropdownButton
                title="Instructor Quality"
                filterData={filterData.instructor_quality}
                defaultFilter={defaultFilters.filterData.instructor_quality}
                clearFilter={clearFilterSearch("instructor_quality")}
            >
                <RangeFilter
                    minRange={0}
                    maxRange={4}
                    step={0.25}
                    filterData={filterData}
                    updateRangeFilter={updateRangeFilter("instructor_quality")}
                    startSearch={conditionalStartSearch}
                    rangeProperty="instructor_quality"
                />
            </DropdownButton>
            <DropdownButton
                title="CU"
                filterData={filterData.cu}
                defaultFilter={defaultFilters.filterData.cu}
                clearFilter={clearFilterSearch("cu")}
            >
                <CheckboxFilter
                    filterData={filterData}
                    updateCheckboxFilter={updateCheckboxFilter}
                    checkboxProperty="cu"
                    startSearch={conditionalStartSearch}
                />
            </DropdownButton>
            <DropdownButton
                title="Type"
                filterData={filterData.activity}
                defaultFilter={defaultFilters.filterData.activity}
                clearFilter={clearFilterSearch("activity")}
            >
                <CheckboxFilter
                    filterData={filterData}
                    updateCheckboxFilter={updateCheckboxFilter}
                    checkboxProperty="activity"
                    startSearch={conditionalStartSearch}
                />
            </DropdownButton>
        </>
    );
    if (mobileView) {
        return (
            <div style={{ marginTop: "0px" }}>
                <div
                    style={{
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        flexWrap: "wrap",
                        background: "white",
                        paddingTop: "20px",
                        paddingBottom: "10px",
                        marginBottom: "10px",
                        borderRadius: "6px",
                    }}
                >
                    <AccountIndicator
                        user={user}
                        login={login}
                        logout={logout}
                        onLeft={true}
                        pathname={router.pathname}
                    />
                    <SearchField
                        setTab={setTab}
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        updateSearchText={updateSearchText}
                    />
                    <div
                        style={{ padding: "0.5rem" }}
                        role="button"
                        onClick={() => showHideReqs(!reqsShown)}
                    >
                        <i className="fas fa-filter" />
                    </div>
                </div>
                {reqsShown && (
                    <div
                        style={{
                            zIndex: 100,
                            marginTop: "-20px",
                            padding: "10px",
                            marginBottom: "20px",
                            display: "flex",
                            width: "100vw",
                            alignItems: "center",
                            flexWrap: "wrap",
                            background: "white",
                            justifyContent: "flex-start",
                        }}
                    >
                        {dropDowns}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="bar level is-mobile" style={{ height: "auto" }}>
            <div className="level-left" style={{ maxWidth: "80vw" }}>
                <div className="level-item">
                    <img
                        src="/icons/favicon.ico"
                        alt=""
                        style={{
                            height: "2.5rem",
                            paddingLeft: "1.5rem",
                        }}
                    />
                </div>
                <div className="level-item" id="searchdiv">
                    <SearchField
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        updateSearchText={updateSearchText}
                    />
                </div>
                <div
                    className="level-item filterContainer"
                    style={{ marginLeft: ".5em" }}
                >
                    <a
                        role="button"
                        onClick={() => setView(0)}
                        style={{
                            backgroundColor: isExpanded ? "white" : "#f0f1f3",
                            padding: ".5em",
                            paddingBottom: "0",
                        }}
                    >
                        <img
                            style={{ width: "1.5em" }}
                            src="/icons/toggle-norm.svg"
                            alt="logo"
                        />
                    </a>
                    <a
                        role="button"
                        onClick={() => setView(1)}
                        style={{
                            backgroundColor: isExpanded ? "#f0f1f3" : "white",
                            padding: ".5em",
                            paddingBottom: "0",
                        }}
                    >
                        <img
                            style={{ width: "1.5em" }}
                            src="/icons/toggle-expanded.svg"
                            alt="logo"
                        />
                    </a>
                </div>
                <div className="level-item filterContainer" id="filterdiv">
                    <span className="icon">
                        <i className="fas fa-filter" />
                    </span>
                    <p> Filter by</p>
                    {dropDowns}
                </div>
            </div>
            <div className="level-right is-hidden-mobile">
                <div className="level-item">
                    <button
                        className="button is-white"
                        style={{
                            marginRight: "1em",
                            color: "#7e7e7e",
                        }}
                        type="button"
                        onClick={() => {
                            clearSearchResults();
                            conditionalStartSearch({
                                // TODO: remove any cast when getting rid of redux
                                ...(defaultFilters.filterData as any),
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
            <div className="level-right">
                <div className="level-item">
                    <AccountIndicator
                        user={user}
                        login={login}
                        backgroundColor="purple"
                        nameLength={1}
                        logout={() => {
                            logout();
                            clearScheduleData();
                        }}
                        onLeft={false}
                        pathname={router.pathname}
                    />
                </div>
            </div>
        </div>
    );
}

//@ts-ignore
const mapStateToProps = (state) => ({
    schoolReq: state.filters.schoolReq,
    filterData: state.filters.filterData,
    defaultReqs: state.filters.defaultReqs,
    isLoadingCourseInfo: state.sections.courseInfoLoading,
    isSearchingCourseInfo: state.sections.searchInfoLoading,
    user: state.login.user,
});

//@ts-ignore
const mapDispatchToProps = (dispatch) => ({
    login: (user: User) => dispatch(login(user)),
    logout: () => dispatch(logout()),
    loadRequirements: () => dispatch(loadRequirements()),
    startSearch: (filterData: FilterData) =>
        dispatch(fetchCourseSearch(filterData)),
    addSchoolReq: (reqID: string) => dispatch(addSchoolReq(reqID)),
    remSchoolReq: (reqID: string) => dispatch(remSchoolReq(reqID)),
    updateSearchText: (s: string) => dispatch(updateSearchText(s)),
    updateRangeFilter: (field: string) => (values: [number, number]) =>
        dispatch(updateRangeFilter(field, values)),
    updateCheckboxFilter: (
        field: string,
        value: string,
        toggleState: boolean
    ) => dispatch(updateCheckboxFilter(field, value, toggleState)),
    clearAll: () => dispatch(clearAll()),
    clearFilter: (propertyName: string) => dispatch(clearFilter(propertyName)),
    clearSearchResults: () => dispatch(updateSearch([])),
    clearScheduleData: () => dispatch(clearAllScheduleData()),
});
//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);
