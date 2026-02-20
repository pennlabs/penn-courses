import React, { FunctionComponent, useState, useEffect } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";
import getCsrf from "../csrf";
import {
    doAPIRequest,
    fetchCourseDetails,
    updateCourseInfo,
    removeSchedItem,
    updateScrollPos,
} from "../../actions/index";

import CourseList from "./CourseList";
import CourseInfo from "./CourseInfo";
import Recs from "../recomendations/Recs";

import { Loading } from "../bulma_derived_components";
import { Course as CourseType, Course, Section, SortMode } from "../../types";

interface SelectorProps {
    courses: Course[];
    course: Course;
    getCourse: (courseId: string) => void;
    clearCourse: () => void;
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
    margin-left: auto;
    margin-right: auto;
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
    const [recCourses, setRecCourses] = useState<CourseType[]>([]);
    // 0 - not loaded, 1 - loaded, 2 - error, 3 - no auth
    const [fetchStatus, setFetchStatus] = useState(0);
    const [refresh, setRefresh] = useState(false);

    // delete func - does nothing for now
    const onClickDelete = () => {};

    useEffect(() => {
        setFetchStatus(0);

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

        doAPIRequest("/plan/recommendations/", requestOptions).then((res) => {
            setRefresh(false);
            if (res.ok) {
                res.json().then((recCoursesResult) => {
                    setRecCourses(recCoursesResult);
                    setFetchStatus(1);
                });
            } else if (res.status === 400) {
                return setFetchStatus(2);
            } else if (res.status === 403) {
                return setFetchStatus(3);
            }
        });
    }, [refresh, setRecCourses, setFetchStatus]);

    const recPanel = (
        <Recs
            showRecs={showRecs}
            setShowRecs={setShowRecs}
            recCourses={recCourses}
            getCourse={getCourse}
            fetchStatus={fetchStatus}
            setRefresh={setRefresh}
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

            {/* recPanel // TODO: re-enable */}
        </>
    );

    const courseList = (
        <CourseList
            sortMode={sortMode}
            courses={courses}
            getCourse={getCourse}
            scrollPos={scrollPos}
            setScrollPos={setScrollPos}
            recCoursesId={recCourses.map((a) => a.id)}
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
                    {/* recPanel // TODO: re-enable */}
                </div>
            </div>
        ) : (
            <>
                {courseList}
                {/* recPanel // TODO: re-enable */}
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
                    {/* recPanel // TODO: re-enable */}
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
    removeFromSchedule: (id: string) => dispatch(removeSchedItem(id)),
    setScrollPos: (scrollPos: number) => dispatch(updateScrollPos(scrollPos)),
});

// no clue why the higher-order connect function isn't working with typescript -- Selector is definitely a component.
// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Selector);
