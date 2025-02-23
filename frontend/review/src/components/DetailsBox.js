import React, { forwardRef, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ColumnSelector, ScoreTable } from "./common";
import {
  compareSemesters,
  getColumnName,
  orderColumns,
  toNormalizedSemester
} from "../utils/helpers";
import { apiHistory } from "../utils/api";
import { PROF_IMAGE_URL } from "../constants/routes";
import { REGISTRATION_METRICS_COLUMNS } from "../constants";

/*
 * Settings objects/object generators for the columns of the DetailsBox
 */

const semesterCol = {
  id: "semester",
  width: 125,
  Header: "Semester",
  accessor: "semester",
  Cell: ({ value, original }) => <center>{value}</center>,
  sortMethod: compareSemesters,
  show: true,
  required: true
};

const nameCol = {
  id: "name",
  width: 250,
  Header: "Name",
  accessor: "name",
  Cell: ({ value, original }) => <center>{value}</center>,
  show: true,
  filterMethod: ({ value }, { name, semester }) =>
    value === "" || // If the filter value is blank, all
    name.toLowerCase().includes(value.toLowerCase()) ||
    semester.toLowerCase().includes(value.toLowerCase())
};

const codeCol = {
  id: "course_code",
  width: 125,
  Header: "Course Code",
  accessor: "course_code",
  Cell: ({ value, original }) => <center>{value}</center>,
  show: true
};

const activityCol = {
  id: "activity",
  Header: "Activity",
  accessor: "activity",
  width: 150,
  Cell: ({ value, original }) => <center>{value}</center>,
  show: true
};

const formsCol = {
  id: "forms",
  width: 150,
  Header: "Forms",
  accessor: "forms_returned",
  show: true,
  required: true,
  Cell: ({ value, original }) =>
    value == null ? (
      <center className="empty">N/A</center>
    ) : (
      <center>
        {value} / {original.forms_produced}{" "}
        <small style={{ color: "#aaa", fontSize: "0.8em" }}>
          ({((value / original.forms_produced) * 100).toFixed(1)}%)
        </small>
      </center>
    )
};

/**
 * The box below the course ratings table that contains student comments and semester information.
 */
export const DetailsBox = forwardRef(
  ({ course, instructor, url_semester, type, isCourseEval }, ref) => {
    const [data, setData] = useState({});
    const [viewingRatings, setViewingRatings] = useState(true);
    const [selectedSemester, setSelectedSemester] = useState(null);
    const [semesterList, setSemesterList] = useState([]);
    const [columns, setColumns] = useState([]);
    const [filtered, setFiltered] = useState([]);
    const [filterAll, setFilterAll] = useState("");
    const [emptyStateImg, setEmptyStateImg] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const showCol = info =>
      REGISTRATION_METRICS_COLUMNS.includes(info) === isCourseEval;

    const generateCol = info => {
      if (!showCol(info)) {
        return null;
      }
      return {
        id: info,
        width: 175,
        Header: getColumnName(info),
        accessor: info,
        show: true,
        Cell: ({ value }) => (
          <center className={value == null ? "empty" : ""}>
            {value == null
              ? "N/A"
              : isNaN(value) && value.slice(-1) === "%"
              ? value
              : isCourseEval
              ? value
              : value.toFixed(2)}
          </center>
        )
      };
    };

    useEffect(() => {
      const num = Math.floor(Math.random() * 5 + 1);
      setEmptyStateImg(PROF_IMAGE_URL(num));
    }, []);
    useEffect(() => {
      setIsLoading(true);
      if (instructor !== null && course !== null) {
        apiHistory(course, instructor, url_semester)
          .then(res => {
            const sections = Object.values(res.sections);
            const fields = [
              ...new Set(
                sections.reduce((r, s) => [...r, ...Object.keys(s.ratings)], [])
              )
            ]; // union of all keys of objects in sections
            const ratingCols = orderColumns(fields)
              .map(generateCol)
              .filter(col => col);
            const semesterSet = new Set(
              sections
                .filter(a => a.comments)
                .map(a => a.semester)
                .sort(compareSemesters)
            );
            const semesters = [...semesterSet];
            setData(res);
            setColumns([
              semesterCol,
              nameCol,
              codeCol,
              activityCol,
              formsCol,
              ...ratingCols
            ]);
            setSemesterList(semesters);
            setSelectedSemester(() => {
              if (!semesters.length) return null;
              return semesterSet.has(selectedSemester)
                ? selectedSemester
                : semesters[0];
            });
          })
          .finally(() => {
            setIsLoading(false);
          });
      }
    }, [course, instructor, selectedSemester]);

    const hasData = Boolean(Object.keys(data).length);
    const hasSelection =
      (type === "course" && instructor) || (type === "instructor" && course);
    const isCourse = type === "course";

    // Return loading component. TODO: Add spinner/ghost loader.
    if (!hasData && hasSelection && isLoading)
      return (
        <div
          id="course-details"
          className="box"
          style={{ textAlign: "center", padding: 45 }}
          ref={ref}
        >
          <i
            className="fa fa-spin fa-cog fa-fw"
            style={{ fontSize: "150px", color: "#aaa" }}
          />
          <h1 style={{ fontSize: "2em", marginTop: 15 }}>Loading...</h1>
        </div>
      );

    // Return placeholder image.
    if (!hasData || !hasSelection)
      return (
        <div
          id="course-details"
          className="box"
          ref={ref}
          style={{ textAlign: "center" }}
        >
          <div>
            <div>
              {isCourse ? (
                <object type="image/svg+xml" data={emptyStateImg} width="175">
                  <img alt="Professor Icon" src={emptyStateImg} />
                </object>
              ) : (
                <object
                  type="image/svg+xml"
                  id="select-course-icon"
                  data="/static/image/books-and-bag.svg"
                  width="250"
                >
                  <img alt="Class Icon" src="/static/image/books-and-bag.png" />
                </object>
              )}
            </div>
          </div>
          <h3
            style={{ color: "#b2b2b2", margin: "1.5em", marginBottom: ".5em" }}
          >
            {isCourse
              ? "Select an instructor to see individual sections, comments, and more details."
              : "Select a course to see individual sections, comments, and more details."}
          </h3>
        </div>
      );

    const {
      instructor: { name },
      sections
    } = data;
    const sectionsList = Object.values(sections);

    return (
      <div id="course-details" className="box" ref={ref}>
        <div id="course-details-wrapper">
          <h3>
            <Link
              style={{ color: "#b2b2b2", textDecoration: "none" }}
              to={isCourse ? `/instructor/${instructor}` : `/course/${course}`}
            >
              {isCourse ? name : course}
            </Link>
          </h3>
          <div className="clearfix">
            <div className="btn-group">
              <button
                onClick={() => setViewingRatings(true)}
                id="view_ratings"
                className={`btn btn-sm ${
                  viewingRatings ? "btn-sub-primary" : "btn-sub-secondary"
                }`}
              >
                Ratings
              </button>
              <button
                onClick={() => setViewingRatings(false)}
                id="view_comments"
                className={`btn btn-sm ${
                  viewingRatings ? "btn-sub-secondary" : "btn-sub-primary"
                }`}
              >
                Comments
              </button>
            </div>
            <ColumnSelector
              name="details"
              onSelect={setColumns}
              columns={columns}
              buttonStyle="btn-sub"
            />
            {viewingRatings && (
              <div className="float-right">
                <label className="table-search">
                  <input
                    type="search"
                    className="form-control form-control-sm"
                    value={filterAll}
                    onChange={({ target: { value } }) => {
                      setFiltered([{ id: "name", value }]);
                      setFilterAll(value);
                    }}
                  />
                </label>
              </div>
            )}
          </div>
          {viewingRatings ? (
            <div id="course-details-data">
              <ScoreTable
                alternating
                ignoreSelect
                sorted={[{ id: "semester", desc: false }]}
                filtered={filtered}
                data={sectionsList.map(
                  ({
                    ratings,
                    semester,
                    course_name: name,
                    course_code,
                    activity,
                    forms_produced,
                    forms_returned
                  }) => ({
                    ...ratings,
                    semester: toNormalizedSemester(semester),
                    name,
                    course_code,
                    activity,
                    forms_produced,
                    forms_returned
                  })
                )}
                columns={columns}
                noun="section"
              />
            </div>
          ) : (
            <div id="course-details-comments" className="clearfix mt-2">
              <div className="list">
                {semesterList.map(sem => (
                  <div
                    key={sem}
                    onClick={() => setSelectedSemester(sem)}
                    className={selectedSemester === sem ? "selected" : ""}
                  >
                    {sem}
                  </div>
                ))}
              </div>
              <div
                className="comments"
                dangerouslySetInnerHTML={{
                  __html:
                    sectionsList
                      .filter(
                        ({ semester, comments }) =>
                          semester === selectedSemester && comments
                      )
                      .map(info => info.comments)
                      .join(", ") ||
                    "This instructor does not have any comments for this course."
                }}
              />
            </div>
          )}
        </div>
      </div>
    );
  }
);

export default DetailsBox;
