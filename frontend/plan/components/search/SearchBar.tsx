import React, { useEffect, useState } from "react";
import { connect } from "react-redux";
import styled from "styled-components";
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

const MobileSearchBarOuterContainer = styled.div`
    margin-bottom: 0;
`;

const MobileSearchBarInnerContainer = styled.div`
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    background: white;
    padding-top: 20px;
    padding-bottom: 10px;
    margin-bottom: 10px;
    border-radius: 6px;
`;

const MobileFilterContainer = styled.div`
    padding: 0.5rem;
`;

const MobileFilterDropdowns = styled.div`
    z-index: 100;
    margin-top: -20px;
    margin-bottom: 20px;
    padding: 10px;
    display: flex;
    width: 100vw;
    align-items: center;
    flex-wrap: wrap;
    background: white;
    justify-content: flex-start;
`;

const SearchBarContainer = styled.div`
    margin: 1rem 1.5rem;
    padding: 0.25rem;
    background-color: white;
    border-radius: 6px;
    box-shadow: 0 1px 3px 0 lightgrey;
    width: inherit;
    align-items: center;
    justify-content: space-between;
    height: auto;
    margin-bottom: 1.5rem;

    @media screen and (min-width: 769px) {
        display: flex;
    }
`;

const SearchBarFilters = styled.div`
    flex-basis: auto;
    flex-grow: 0;
    flex-shrink: 0;
    align-items: center;
    justify-content: flex-start;
    max-width: 80vw !important;

    @media screen and (min-width: 769px) {
        display: flex;
    }
`;

const ClearContainer = styled.div`
    flex-basis: auto;
    flex-grow: 0;
    flex-shrink: 0;
    align-items: center;
    justify-content: flex-end;
    display: none;

    @media screen and (min-width: 769px) {
        display: flex;
    }
`;

const LevelItem = styled.div`
    align-items: center;
    display: flex;
    flex-basis: auto;
    flex-grow: 0;
    flex-shrink: 0;
    justify-content: center;
    margin-right: 0.75rem;
`;

const FilterLevelItem = styled.div`
    align-items: center;
    flex-basis: auto;
    flex-shrink: 0;
    flex-grow: 1;
    flex-wrap: wrap;
    padding: 0.3em 0em;
    justify-content: flex-start;
    max-width: calc(100% - 17rem);
    display: flex;
    margin-right: 0.75rem;

    > * {
        padding-right: 0.5rem;
    }
`;

const PlanViewButton = styled.a`
    background-color: ${({
        isExpanded,
        expandedButton,
    }: {
        isExpanded: boolean;
        expandedButton: boolean;
    }) => (isExpanded === expandedButton ? "white" : "#f0f1f3")};
    padding: 0.5em;
    padding-bottom: 0;

    img {
        width: 1.5em;
    }
`;

const ClearButton = styled.button`
    user-select: none;
    align-items: center;
    border: 1px solid transparent;
    border-radius: 4px;
    box-shadow: none;
    display: inline-flex;
    font-size: 1rem;
    height: 2.25em;
    line-height: 1.5;
    position: relative;
    vertical-align: top;
    border-width: 1px;
    cursor: pointer;
    justify-content: center;
    padding-bottom: calc(0.375em - 1px);
    padding-left: 0.75em;
    padding-right: 0.75em;
    padding-top: calc(0.375em - 1px);
    text-align: center;
    white-space: nowrap;
    background-color: white;
    border-color: transparent;
    margin-right: 1em;
    color: #7e7e7e;
`;

const PCPImage = styled.img`
    height: 2.5rem;
    padding-left: 1.5rem;
`;

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
            <MobileSearchBarOuterContainer>
                <MobileSearchBarInnerContainer>
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
                    <MobileFilterContainer
                        role="button"
                        onClick={() => showHideReqs(!reqsShown)}
                    >
                        <i className="fas fa-filter" />
                    </MobileFilterContainer>
                </MobileSearchBarInnerContainer>
                {reqsShown && (
                    <MobileFilterDropdowns>{dropDowns}</MobileFilterDropdowns>
                )}
            </MobileSearchBarOuterContainer>
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
