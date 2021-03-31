import React, { FunctionComponent, useState, useEffect } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import getCsrf from "../csrf";

import CourseList from "./CourseList";
import CourseInfo from "./CourseInfo";
import Recs from "../recomendations/Recs";
import { Course as CourseType } from "../../types";

import { Loading } from "../bulma_derived_components";

import {
    fetchCourseDetails,
    updateCourseInfo,
    addSchedItem,
    removeSchedItem,
    updateScrollPos,
} from "../../actions";
import { Course, Section, SortMode } from "../../types";

interface SelectorProps {
    courses: Course[];
    course: Course;
    getCourse: (courseId: string) => void;
    clearCourse: () => void;
    addToSchedule: (section: string) => void;
    removeFromSchedule: (id: string) => void;
    isLoadingCourseInfo: boolean;
    isSearchingCourseInfo: boolean;
    view: number;
    scrollPos: number;
    setScrollPos: (scrollPos: number) => void;
    sortMode: SortMode;
    mobileView: boolean;
}

const EmptyResultsContainer = styled.div`
    font-size: 0.8rem;
    text-align: center;
    margin-top: 5vh;
    max-width: 45vh;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
    overflow: hidden;
`;

const Selector: FunctionComponent<SelectorProps> = ({
    courses,
    course,
    getCourse,
    clearCourse,
    addToSchedule,
    removeFromSchedule,
    isLoadingCourseInfo,
    isSearchingCourseInfo,
    sortMode,
    view,
    scrollPos,
    setScrollPos,
}: SelectorProps) => {
    const isExpanded = view === 1;
    const isLoading =
        isSearchingCourseInfo || (isLoadingCourseInfo && !isExpanded);

    const [showRecs, setShowRecs] = useState(true);
    const [recCourses, setRecCourses] = useState([]);
    const [recLoaded, setRecLoaded] = useState(false);
    const [removeRec, setRemoveRec] = useState(true);

    //delete func - does nothing for now
    const onClickDelete = () => {};

    useEffect(() => {
        setRecLoaded(false);

        console.log(recLoaded);

        const requestOptions = {
            method: "POST",
            credentials: "include",
            mode: "same-origin",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrf(),
            },
            body: JSON.stringify({}),
        };

        //@ts-ignore Not sure why this is not typechecking
        fetch(`/api/plan/recommendations/`, requestOptions).then((res) =>
            res.json().then((recCoursesResult) => {
                console.log(recCoursesResult);
                setRecCourses(recCoursesResult);

                setRecLoaded(true);
                console.log(recLoaded);
            })
        );
    }, [removeRec]);

    let recPanel = (
        <Recs
            showRecs={showRecs}
            setShowRecs={setShowRecs}
            recCourses={recCourses}
            getCourse={getCourse}
            onClickDelete={onClickDelete}
        />
    );

    let element = (
        <>
            <EmptyResultsContainer>
                <img
                    src="/icons/empty-state-search.svg"
                    alt=""
                    style={{
                        height: "auto",
                        maxWidth: "70%",
                        maxHeight: "18.75rem",
                    }}
                />
                <h3
                    style={{
                        fontWeight: "bold",
                        marginBottom: "0.5rem",
                    }}
                >
                    No result found
                </h3>
                Search for courses, departments, or instructors above. Looking
                for something specific? Try using the filters!
            </EmptyResultsContainer>

            {recPanel}
        </>
    );

    const courseList = (
        <CourseList
            sortMode={sortMode}
            courses={courses}
            getCourse={getCourse}
            scrollPos={scrollPos}
            setScrollPos={setScrollPos}
        />
    );

    if (courses.length > 0 && !course) {
        element = isExpanded ? (
            <div className="columns">
                <div
                    className="column is-one-third"
                    style={{
                        height: "calc(100vh - 12.5em)",
                        borderRight: "1px solid #dddddd",
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    {courseList}
                    {recPanel}
                </div>
            </div>
        ) : (
            <>
                {courseList}
                {recPanel}
            </>
        );
    }

    if (course) {
        element = isExpanded ? (
            <div className="columns">
                <div
                    className="column is-one-third"
                    style={{
                        height: "calc(100vh - 12.5em)",
                        borderRight: "1px solid #dddddd",
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    {courseList}
                    {recPanel}
                </div>
                <div
                    className="column is-two-thirds"
                    style={{ height: "calc(100vh - 12.5em)" }}
                >
                    {isLoadingCourseInfo ? (
                        <Loading />
                    ) : (
                        <CourseInfo
                            getCourse={getCourse}
                            course={course}
                            view={view}
                        />
                    )}
                </div>
            </div>
        ) : (
            <>
                <CourseInfo
                    getCourse={getCourse}
                    course={course}
                    back={clearCourse}
                    view={view}
                />
            </>
        );
    }
    return <>{isLoading ? <Loading /> : element}</>;
};

const mapStateToProps = ({
    sections: {
        scrollPos,
        sortMode,
        searchResults,
        course,
        courseInfoLoading: isLoadingCourseInfo,
        searchInfoLoading: isSearchingCourseInfo,
    },
}: any) => ({
    courses: searchResults.filter(({ num_sections: num }: Course) => num > 0),
    course,
    scrollPos,
    sortMode,
    isLoadingCourseInfo,
    isSearchingCourseInfo,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    getCourse: (courseId: string) => dispatch(fetchCourseDetails(courseId)),
    clearCourse: () => dispatch(updateCourseInfo(null)),
    addToSchedule: (section: Section) => dispatch(addSchedItem(section)),
    removeFromSchedule: (id: string) => dispatch(removeSchedItem(id)),
    setScrollPos: (scrollPos: number) => dispatch(updateScrollPos(scrollPos)),
});

// no clue why the higher-order connect function isn't working with typescript -- Selector is definitely a component.
// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Selector);
