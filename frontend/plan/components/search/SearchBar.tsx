import React, { useEffect, useState } from "react";
import { connect } from "react-redux";
import styled from "styled-components";
// TODO: Move shared components to typescript
// @ts-ignore
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import { useRouter } from "next/router";
import { DropdownButton } from "./DropdownButton";
import { ButtonFilter } from "./ButtonFilter";
import { SchoolReq } from "./SchoolReq";
import { RangeFilter } from "./RangeFilter";
import { CheckboxFilter } from "./CheckboxFilter";
import { DayTimeFilter } from "./DayTimeFilter";
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
    updateButtonFilter,
    clearAll,
    clearFilter,
    updateSearch,
    clearAllScheduleData,
} from "../../actions";
import { login, logout } from "../../actions/login";

const DAY_TIME_ENABLED = true;

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
    setShowLoginModal: React.Dispatch<React.SetStateAction<boolean>>;
    activeSchedule: { id: number };
    updateButtonFilter: (field: string) => (value: number) => void;
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
    color: #c6c6c6;
`;

const MobileFilterDropdowns = styled.div`
    z-index: 100;
    margin-top: -20px;
    padding: 5px 10px;
    padding-bottom: 5px;
    display: flex;
    width: 100vw;
    align-items: center;
    flex-wrap: wrap;
    background: white;
    justify-content: flex-start;
`;

const ClearContainer = styled.div`
    z-index: 100;
    padding: 10px;
    padding-top: 0px;
    display: flex;
    width: 100vw;
    align-items: center;
    flex-wrap: wrap;
    background: white;
    justify-content: center;
`;

const SearchBarContainer = styled.div`
    padding: 0.5rem 0.25rem;
    background-color: white;
    box-shadow: 0 1px 3px 0 lightgrey;
    width: inherit;
    align-items: center;
    justify-content: space-between;
    height: auto;
    margin-bottom: 2rem;

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

const SearchLevelItem = styled(LevelItem)`
    padding-left: 0.5rem;
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
    padding-left: 0.5rem;

    > * {
        padding-right: 0.5rem;
    }
`;

const LevelRight = styled.div`
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-basis: auto;
    flex-grow: 0;
    flex-shrink: 0;

    ${LevelItem} {
        margin-right: 0 !important;
    }
`;

const PlanViewButton = styled.a<{
    $isExpanded: boolean;
    $expandedButton: boolean;
}>`
    background-color: ${({
        $isExpanded,
        $expandedButton,
    }: {
        $isExpanded: boolean;
        $expandedButton: boolean;
    }) => ($isExpanded === $expandedButton ? "white" : "#f0f1f3")};
    padding: 0.5em 0.5em 0;

    img {
        width: 1.5em;
    }
`;

const ClearButton = styled.button`
    user-select: none;
    align-items: center;
    border-radius: 4px;
    box-shadow: none;
    display: inline-flex;
    height: 2.25em;
    line-height: 1.5;
    position: relative;
    vertical-align: top;
    cursor: pointer;
    justify-content: center;
    padding: calc(0.375em - 1px) 0em;
    text-align: center;
    white-space: nowrap;
    background-color: white;
    border: 1px solid transparent;
    margin-right: 1em;
    color: #7e7e7e;
    font-size: 0.75rem !important;
`;

const PCPImage = styled.img`
    height: 2.5rem;
    padding-left: 1.5rem;
`;

const MobilePCPImage = styled.img`
    height: 2.5rem;
    padding-left: 0;
    padding-right: 2.5rem;
`;

const Icon = styled.span`
    align-items: center;
    display: inline-flex;
    justify-content: center;
    height: 1.5rem;
    width: 1.5rem;
    pointer-events: none;
`;

const DropdownContainer = styled.div`
    max-width: 60vw !important;
    display: flex;
    flex-direction: row;
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
    setShowLoginModal,
    updateButtonFilter,
    activeSchedule,
}: /* eslint-enable no-shadow */
SearchBarProps) {
    const router = useRouter();

    //TODO: Add requirements support back
    // useEffect(() => {
    //     loadRequirements();
    // }, [loadRequirements]);

    useEffect(() => {
        // ensure that the user is logged in before initiating the sync
        if (user && storeLoaded) {
            clearScheduleData();
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
        if (property === "selectedReq") {
            conditionalStartSearch({
                ...filterData,
                selectedReq: defaultReqs,
            });
        } else {
            conditionalStartSearch({
                ...filterData,
                // @ts-ignore
                [property]: defaultFilters.filterData[property],
            });
        }
    };
    // TODO: find less hacky way of combining date and time into single object
    const filterDataDayTime: any = {
        ...JSON.parse(JSON.stringify(filterData.days)),
        time: filterData.time,
    };
    const initialDayTime: {
        M: boolean;
        T: boolean;
        W: boolean;
        R: boolean;
        F: boolean;
        S: boolean;
        U: boolean;
        time: [number, number];
    } = {
        M: true,
        T: true,
        W: true,
        R: true,
        F: true,
        S: true,
        U: true,
        time: [1.5, 17],
    };

    const dropDowns = (
        <DropdownContainer>
            {/* <DropdownButton
                title="Requirements"
                filterData={filterData.selectedReq}
                defaultFilter={defaultReqs}
                    addSchoolReq={addSchoolReq}
                    remSchoolReq={remSchoolReq}
                />
            </DropdownButton> // TODO: re-enable */}
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
            {DAY_TIME_ENABLED && (
                <DropdownButton
                    title="Day/Time"
                    filterData={filterDataDayTime}
                    defaultFilter={initialDayTime}
                    clearFilter={() => {
                        clearFilterSearch("days")();
                        clearFilterSearch("time")();
                    }}
                >
                    <DayTimeFilter
                        // @ts-ignore
                        filterData={filterData}
                        updateCheckboxFilter={updateCheckboxFilter}
                        checkboxProperty="days"
                        // @ts-ignore
                        startSearch={conditionalStartSearch}
                        minRange={1.5}
                        maxRange={17}
                        step={1 / 60}
                        updateRangeFilter={updateRangeFilter("time")}
                        rangeProperty="time"
                    />
                </DropdownButton>
            )}
            {activeSchedule && (
                <ButtonFilter
                    title="Fit Schedule"
                    filterData={filterData}
                    clearFilter={clearFilterSearch("schedule-fit")}
                    // @ts-ignore
                    startSearch={conditionalStartSearch}
                    value={activeSchedule.id}
                    buttonProperty="schedule-fit"
                    updateButtonFilter={updateButtonFilter("schedule-fit")}
                ></ButtonFilter>
            )}
            <ButtonFilter
                title="Is Open"
                filterData={filterData}
                clearFilter={clearFilterSearch("is_open")}
                // @ts-ignore
                startSearch={conditionalStartSearch}
                value={1}
                buttonProperty="is_open"
                updateButtonFilter={updateButtonFilter("is_open")}
            ></ButtonFilter>
        </DropdownContainer>
    );
    if (mobileView) {
        return (
            <MobileSearchBarOuterContainer>
                <MobileSearchBarInnerContainer>
                    {/* <MobilePCPImage src="/icons/favicon.ico" alt="" /> */}
                    <AccountIndicator
                        user={user}
                        login={(u: User) => {
                            login(u);
                            setShowLoginModal(false);
                        }}
                        logout={() => {
                            logout();
                            clearScheduleData();
                            setShowLoginModal(true);
                        }}
                        leftAligned={true}
                        pathname={router.pathname}
                    />
                    <SearchField
                        setTab={setTab}
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        mobileView={mobileView}
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
                    <>
                        <MobileFilterDropdowns>
                            {dropDowns}
                        </MobileFilterDropdowns>
                        <ClearContainer>
                            <ClearButton
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
                            </ClearButton>
                        </ClearContainer>
                    </>
                )}
            </MobileSearchBarOuterContainer>
        );
    }

    return (
        <SearchBarContainer>
            <SearchBarFilters>
                <LevelItem>
                    <PCPImage src="/icons/favicon.ico" alt="" />
                </LevelItem>
                <SearchLevelItem>
                    <SearchField
                        startSearch={conditionalStartSearch}
                        filterData={filterData}
                        updateSearchText={updateSearchText}
                    />
                </SearchLevelItem>
                <LevelItem
                    className="filterContainer"
                    style={{ marginLeft: ".5em" }}
                >
                    <PlanViewButton
                        role="button"
                        onClick={() => setView(0)}
                        $isExpanded={isExpanded}
                        $expandedButton={true}
                    >
                        <img
                            style={{ width: "1.5em" }}
                            src="/icons/toggle-norm.svg"
                            alt="logo"
                        />
                    </PlanViewButton>
                    <PlanViewButton
                        role="button"
                        onClick={() => setView(1)}
                        $isExpanded={isExpanded}
                        $expandedButton={false}
                    >
                        <img
                            style={{ width: "1.5em" }}
                            src="/icons/toggle-expanded.svg"
                            alt="logo"
                        />
                    </PlanViewButton>
                </LevelItem>
                <FilterLevelItem>
                    <Icon>
                        <i
                            className="fas fa-filter"
                            style={{ color: "#c6c6c6" }}
                        />
                    </Icon>
                    <p> Filter by</p>
                    {dropDowns}
                </FilterLevelItem>
                <LevelRight className="is-hidden-mobile">
                    <LevelItem>
                        <ClearButton
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
                        </ClearButton>
                    </LevelItem>
                </LevelRight>
            </SearchBarFilters>
            <LevelRight>
                <LevelItem>
                    <AccountIndicator
                        user={user}
                        login={(u: User) => {
                            login(u);
                            setShowLoginModal(false);
                        }}
                        backgroundColor="purple"
                        nameLength={1}
                        logout={() => {
                            logout();
                            clearScheduleData();
                            setShowLoginModal(true);
                        }}
                        leftAligned={false}
                        pathname={router.pathname}
                    />
                </LevelItem>
            </LevelRight>
        </SearchBarContainer>
    );
}

// @ts-ignore
const mapStateToProps = (state) => ({
    schoolReq: state.filters.schoolReq,
    filterData: state.filters.filterData,
    defaultReqs: state.filters.defaultReqs,
    isLoadingCourseInfo: state.sections.courseInfoLoading,
    isSearchingCourseInfo: state.sections.searchInfoLoading,
    user: state.login.user,
    activeSchedule: state.schedule.schedules[state.schedule.scheduleSelected],
});

// @ts-ignore
const mapDispatchToProps = (dispatch) => ({
    login: (user: User) => dispatch(login(user)),
    logout: () => dispatch(logout()),
    clearAllScheduleData: () => dispatch(clearAllScheduleData()),
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
    updateButtonFilter: (field: string) => (value: number) =>
        dispatch(updateButtonFilter(field, value)),
    clearAll: () => dispatch(clearAll()),
    clearFilter: (propertyName: string) => dispatch(clearFilter(propertyName)),
    clearSearchResults: () => dispatch(updateSearch([])),
    clearScheduleData: () => dispatch(clearAllScheduleData()),
});
// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(SearchBar);
