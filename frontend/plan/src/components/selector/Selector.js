import React from "react";
import PropTypes from "prop-types";

import connect from "react-redux/es/connect/connect";

import "../../styles/selector.css";

import CourseList from "./CourseList";
import CourseInfo from "./CourseInfo";
import SearchSortDropdown from "../search/SearchSortDropdown";

import {
    fetchCourseDetails, updateCourseInfo, addSchedItem, removeSchedItem
} from "../../actions";

function Selector(props) {
    const {
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
        mobileView,
    } = props;

    const isLoading = isSearchingCourseInfo || (isLoadingCourseInfo && view === 0);

    const loadingIndicator = (
        <div
            className="button is-loading"
            style={{
                height: "85%", width: "100%", border: "none", fontSize: "3rem",
            }}
        />
    );

    const header = (
        <div>
            <span style={{
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-between",
                padding: "1em",
                paddingBottom: "0.4em",
            }}
            >
                <h3 style={{
                    display: "flex",
                    fontWeight: "bold",
                    marginBottom: "0.5rem",
                }}
                >
                Search Results
                </h3>
                <div style={{
                    float: "right",
                    display: "flex",
                    height: "1.5em",
                }}
                >
                    <SearchSortDropdown />
                </div>
            </span>
        </div>
    );

    let element = (
        <div style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
            maxWidth: "45vh",
        }}
        >
            <img src="/icons/empty-state-search.svg" />
            <h3 style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
            >
                No result found
            </h3>
            Search for courses, departments, or instructors above.
            Looking for something specific? Try using the filters!
        </div>
    );

    const courseList = (
        <CourseList
            sortMode={sortMode}
            isLoading={isLoadingCourseInfo}
            courses={courses}
            getCourse={getCourse}
        />
    );

    if (view === 1) {
        element = (
            <div style={{ display: "grid", gridTemplateColumns: "33% 67%" }}>
                <div style={{ height: "calc(100vh - 8em)", borderRight: "1px solid #dddddd" }}>
                    {header}
                    {isSearchingCourseInfo ? loadingIndicator : courseList}
                </div>
                {(!isSearchingCourseInfo && (course || isLoadingCourseInfo))
              && (
                  <div style={{ height: "calc(100vh - 8em)", paddingTop: "1em" }}>
                      {isLoadingCourseInfo ? loadingIndicator
                          : (
                              <CourseInfo
                                  getCourse={getCourse}
                                  course={course}
                                  view={view}
                                  manage={{
                                      addToSchedule,
                                      removeFromSchedule,
                                  }}
                              />
                          )
                      }
                  </div>
              )
                }
            </div>
        );
    } else {
        if (courses.length > 0 && !course) {
            element = (
                <div style={mobileView ? {} : { height: "calc(100vh - 8em)" }}>
                    {header}
                    {courseList}
                </div>
            );
        }
        if (course) {
            element = (
                <CourseInfo
                    getCourse={getCourse}
                    course={course}
                    back={clearCourse}
                    manage={{
                        addToSchedule,
                        removeFromSchedule,
                    }}
                />
            );
        }
    }

    return (
        <>
            {(view === 0 && isLoading) ? loadingIndicator : element}
        </>
    );
}

Selector.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    course: PropTypes.objectOf(PropTypes.any),
    getCourse: PropTypes.func.isRequired,
    clearCourse: PropTypes.func,
    addToSchedule: PropTypes.func,
    sortMode: PropTypes.string,
    removeFromSchedule: PropTypes.func,
    isLoadingCourseInfo: PropTypes.bool,
    isSearchingCourseInfo: PropTypes.bool,
    view: PropTypes.number,
    mobileView: PropTypes.bool,
};

const mapStateToProps = state => (
    {
        courses: state.sections.searchResults.filter(course => course.num_sections > 0),
        course: state.sections.course,
        sortMode: state.sections.sortMode,
        isLoadingCourseInfo: state.sections.courseInfoLoading,
        isSearchingCourseInfo: state.sections.searchInfoLoading,
    }
);


const mapDispatchToProps = dispatch => (
    {
        getCourse: courseId => dispatch(fetchCourseDetails(courseId)),
        clearCourse: () => dispatch(updateCourseInfo(null)),
        addToSchedule: section => dispatch(addSchedItem(section)),
        removeFromSchedule: id => dispatch(removeSchedItem(id)),
    }
);

export default connect(mapStateToProps, mapDispatchToProps)(Selector);
