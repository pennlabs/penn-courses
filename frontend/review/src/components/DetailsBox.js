import React, { forwardRef, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ColumnSelector, ScoreTable, Comment } from "./common";
import {
  compareSemesters,
  getColumnName,
  orderColumns,
  toNormalizedSemester
} from "../utils/helpers";
import { apiComments, apiHistory, apiUserComment } from "../utils/api";
import { PROF_IMAGE_URL } from "../constants/routes";
import { REGISTRATION_METRICS_COLUMNS } from "../constants";
import { WriteComment } from "./Comments/WriteComment";

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
    const [ viewRatings, setViewRatings ] = useState(false);

    return (
      <>
        <div className="tab-wrapper">
          <button className={`btn tab ${viewRatings ? "active" : ""}`} onClick={() => setViewRatings(true)}>Ratings</button>
          <button className={`btn tab ${viewRatings ? "" : "active"}`} onClick={() => setViewRatings(false)}>Comments</button>
        </div>
        <RatingsTab 
          course={course} 
          instructor={instructor} 
          url_semester={url_semester} 
          type={type} 
          isCourseEval={isCourseEval}
          ref={ref} 
          active={viewRatings}
        />
        <CommentsTab 
          course={course} 
          instructor={instructor} 
          url_semester={url_semester} 
          type={type} 
          isCourseEval={isCourseEval}
          ref={ref}
          active={!viewRatings}
        />
      </>
    )
  }
);

const CommentsTab = forwardRef(
  ({ course, instructor, url_semester, type, isCourseEval, active }, ref) => {
    const [semesterList, setSemesterList] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const [comments, setComments] = useState({});
    const [userComment, setUserComment] = useState({});

    const [selectedSemester, setSelectedSemester] = useState(null);

    useEffect(() => {
      setIsLoading(true);
      apiComments(course, "all", null, null)
        .then(res => {
          console.log("fetching comments now", res);
          setComments(res.comments.map(c => ({ ...c, created_at: new Date(c.created_at), modified_at: new Date(c.modified_at) })));
          setSemesterList(res.semesters);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }, [course]);

    useEffect(() => {
      apiUserComment(course).then(res => {
        setUserComment(res);
      });
    }, [course]);

    const hasComments = comments.length > 0;
    const hasUserComment = Object.keys(userComment).length > 0;

    if(!active) return <></>

    if (!hasComments && !hasUserComment) {
      if (isLoading) {
        // Loading spinner
        return <Loading />
      } else {
        // Return placeholder image.
        return (
          <div
            id="course-details"
            className="box"
            ref={ref}
            style={{ textAlign: "center" }}
          >
            <WriteComment 
              course={course} 
              setUserComment={setUserComment} 
            />
            <div>
              <div>
                <object
                  type="image/svg+xml"
                  id="select-course-icon"
                  data="/static/image/books-and-bag.svg"
                  width="250"
                >
                  <img alt="Class Icon" src="/static/image/books-and-bag.png" />
                </object>
              </div>
            </div>
            <h3
              style={{
                color: "#b2b2b2",
                margin: "1.5em",
                marginBottom: ".5em"
              }}
            >
              No one's commented yet! Be the first to share your thoughts.
            </h3>
          </div>
        );
      }
    }

    return (
      <div id="course-details" className="box" ref={ref}>
        <div id="course-details-wrapper">
          <h3>Comments</h3>
          <div id="course-details-comments" className="clearfix mt-2">
            {hasUserComment || 
              <WriteComment 
                course={course} 
                semesters={semesterList} 
                setUserComment={setUserComment} 
              />}
            <div className="list">
              <div
                onClick={() => setSelectedSemester(null)}
                className={selectedSemester === null ? "selected" : ""}
              >
                Overall
              </div>
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
            <div className="comments">
              {hasUserComment && <Comment comment={userComment} isUserComment />}
              {comments
                .filter(
                  c => !selectedSemester || c.semester === selectedSemester
                )
                .map(c => (
                  <Comment comment={c} />
                ))}
            </div>
            
          </div>
          <div>
              <button className="btn">1</button>
              <button className="btn">2</button>
              <button className="btn">3</button>
              <button className="btn">4</button>
            </div>
        </div>
      </div>
    );
  }
);

const RatingsTab = forwardRef(
  ({ course, instructor, url_semester, type, isCourseEval, active }, ref) => {
    const hasSelection =
      (type === "course" && instructor) || (type === "instructor" && course);
    // Return placeholder image.
    if (!hasSelection && active) {
      return <Placeholder type={type} ref={ref} />
    }

    const [data, setData] = useState({});
    const [columns, setColumns] = useState([]);
    const [filtered, setFiltered] = useState([]);
    const [filterAll, setFilterAll] = useState("");
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
      setIsLoading(true);
      if (instructor !== null && course !== null) {
        apiHistory(course, instructor, url_semester)
          .then(res => {
            console.log("fetching ratings");
            const sections = Object.values(res.sections);
            const fields = [
              ...new Set(
                sections.reduce((r, s) => [...r, ...Object.keys(s.ratings)], [])
              )
            ]; // union of all keys of objects in sections
            const ratingCols = orderColumns(fields)
              .map(generateCol)
              .filter(col => col);
            setData(res);
            setColumns([
              semesterCol,
              nameCol,
              codeCol,
              activityCol,
              formsCol,
              ...ratingCols
            ]);
          })
          .finally(() => {
            setIsLoading(false);
          });
      }
    }, [course, instructor, url_semester]);

    const hasData = Boolean(Object.keys(data).length);
    const isCourse = type === "course";


    if(!active) return <></>

    // Return loading component. TODO: Add spinner/ghost loader.
    if (!hasData && hasSelection && isLoading) {
      return <Loading />
    }
    // Return placeholder image.
    if (!hasData) {
      return <Placeholder type={type} ref={ref} />;
    }

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
            <ColumnSelector
              name="details"
              onSelect={setColumns}
              columns={columns}
              buttonStyle="btn-sub"
            />
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
          </div>
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
        </div>
      </div>
    );
  }
);

const Placeholder = forwardRef(({ type }, ref) => {
  const [emptyStateImg, setEmptyStateImg] = useState("");

  useEffect(() => {
    const num = Math.floor(Math.random() * 5 + 1);
    setEmptyStateImg(PROF_IMAGE_URL(num));
  }, []);

  return (
    <div
      id="course-details"
      className="box"
      ref={ref}
      style={{ textAlign: "center" }}
    >
      <div>
        <div>
          {type === "course" ? (
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
        {type === "course"
          ? "Select an instructor to see individual sections, comments, and more details."
          : "Select a course to see individual sections, comments, and more details."}
      </h3>
    </div>
  );
})

const Loading = forwardRef(({ type }, ref) => {
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
});

export default DetailsBox;
