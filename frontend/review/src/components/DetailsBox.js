import React, { forwardRef, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ColumnSelector, ScoreTable } from "./common";
import { Comment, WriteComment } from "./Comments";
import { Dropdown } from "./common/Dropdown";
import {
  compareSemesters,
  getColumnName,
  orderColumns,
  toNormalizedSemester,
} from "../utils/helpers";
import {
  apiComments,
  apiHistory,
  apiComment,
  getOwnComment,
} from "../utils/api";
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
  required: true,
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
    semester.toLowerCase().includes(value.toLowerCase()),
};

const codeCol = {
  id: "course_code",
  width: 125,
  Header: "Course Code",
  accessor: "course_code",
  Cell: ({ value, original }) => <center>{value}</center>,
  show: true,
};

const activityCol = {
  id: "activity",
  Header: "Activity",
  accessor: "activity",
  width: 150,
  Cell: ({ value, original }) => <center>{value}</center>,
  show: true,
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
    ),
};

/**
 * The box below the course ratings table that contains student comments and semester information.
 */
export const DetailsBox = forwardRef(
  ({ course, instructor, url_semester, type, isCourseEval }, ref) => {
    const [viewRatings, setViewRatings] = useState(false);

    return (
      <>
        <div className="tab-wrapper">
          <button
            className={`btn tab ${viewRatings ? "active" : ""}`}
            onClick={() => setViewRatings(true)}
          >
            Ratings
          </button>
          <button
            className={`btn tab ${viewRatings ? "" : "active"}`}
            onClick={() => setViewRatings(false)}
          >
            Comments
          </button>
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
    );
  }
);

const CommentsTab = forwardRef(
  ({ course, instructor, url_semester, type, isCourseEval, active }, ref) => {
    const [semesterList, setSemesterList] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [data, setData] = useState({});
    const [reply, setReply] = useState(null);
    const [page, setPage] = useState(1);
    const [maxPage, setMaxPage] = useState(1);
    const [comments, setComments] = useState([]);
    const [userComment, setUserComment] = useState({});
    const [selectedSemester, setSelectedSemester] = useState(null);

    const hasSelection =
      (type === "course" && instructor) || (type === "instructor" && course);

    useEffect(() => {
      const semester = selectedSemester ? selectedSemester : "all";
      setIsLoading(true);
      getOwnComment(course, semester, instructor, null)
        .then((ownComments) => {
          console.log("fetching own comments now", ownComments);
          if (
            ownComments &&
            ownComments.comments &&
            ownComments.comments.length > 0
          ) {
            const parentComments = ownComments.comments.filter(
              (c) => c.id === c.base
            );
            console.log("parent comments", parentComments);
            if (parentComments.length > 0) {
              var userComment = parentComments[0];
              userComment = {
                ...userComment,
                created_at: new Date(userComment.created_at),
                modified_at: new Date(userComment.modified_at),
              };
              setUserComment(userComment);
            }
          } else {
            setUserComment({});
          }
          apiComments(course, semester, instructor, null, page)
            .then((res) => {
              console.log("fetching comments now", res);
              setComments(
                res.comments.map((c) => ({
                  ...c,
                  created_at: new Date(c.created_at),
                  modified_at: new Date(c.modified_at),
                }))
              );
              setSemesterList(res.semesters);
              setMaxPage(res.num_pages);
              console.log("semester rest", res);
            })
            .catch((err) => {
              console.log("error", err);
            })
            .finally(() => {
              setIsLoading(false);
            });
        })
        .catch((err) => {
          console.log("error", err);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }, [course, instructor, selectedSemester, page]);

    useEffect(() => {
      if (instructor !== null && course !== null) {
        apiHistory(course, instructor, url_semester).then((res) => {
          console.log("fetching ratings");
          console.log("data", res);
          setData(res);
        });
      }
    }, [course, instructor, url_semester]);

    useEffect(() => {
      // TODO: HARDCODED USER ID BC CANT YET FETCH WHICH COMMENT BELONGS TO WHICH USER
      // apiComment("10").then(res => {
      //   setUserComment(res);
      // });
    }, [course]);

    const hasData = Boolean(Object.keys(data).length);
    const isCourse = type === "course";

    if (!hasSelection && active) {
      return <Placeholder type={type} ref={ref} />;
    }

    if (!active) return <></>;

    // Return loading component. TODO: Add spinner/ghost loader.
    if (!hasData && hasSelection && isLoading) {
      return <Loading />;
    }
    // Return placeholder image.
    if (!hasData) {
      return <Placeholder type={type} ref={ref} />;
    }

    // const {
    //   instructor: { name },
    //   sections,
    // } = data;
    // const sectionsList = Object.values(sections);

    const hasComments = comments.length > 0;
    const hasUserComment = Object.keys(userComment).length > 0;

    console.log(semesterList);
    console.log("logged_in_user");
    // if (!active) return <></>;

    if (!hasComments && !hasUserComment) {
      if (isLoading) {
        // Loading spinner
        return <Loading />;
      } else {
        // Return placeholder image.
        return (
          <div
            id="course-details"
            className="box"
            ref={ref}
            style={{ textAlign: "center" }}
          >
            <div id="course-details-wrapper">
              <h3>
                <Link
                  style={{ color: "#b2b2b2", textDecoration: "none" }}
                  to={data ? `/instructor/${instructor}` : `/course/${course}`}
                >
                  {isCourse ? data.instructor.name : course}
                </Link>
              </h3>

              <WriteComment
                course={course}
                instructor={instructor}
                setUserComment={setUserComment}
                semestersList={data.sections}
              />

              <div className="mt-2">
                <div>
                  <object
                    type="image/svg+xml"
                    id="select-course-icon"
                    data="/static/image/books-and-bag.svg"
                    width="250"
                  >
                    <img
                      alt="Class Icon"
                      src="/static/image/books-and-bag.png"
                    />
                  </object>
                </div>
              </div>
              <h3
                style={{
                  color: "#b2b2b2",
                  margin: "1.5em",
                  marginBottom: ".5em",
                }}
              >
                No one's commented yet! Be the first to share your thoughts.
              </h3>
            </div>
          </div>
        );
      }
    }

    return (
      <div id="course-details" className="box" ref={ref}>
        <div id="course-details-wrapper">
          <h3>{isCourse ? data.instructor.name : "Comments"}</h3>
          <div className="clearfix mt-2">
            <div id="course-details-comments" className="clearfix mt-2">
              <div>
                <div>
                  {!hasUserComment ? (
                    <WriteComment
                      course={course}
                      semesters={semesterList}
                      instructor={instructor}
                      setUserComment={setUserComment}
                      semestersList={data.sections}
                      setReply={setReply}
                    />
                  ) : reply !== null ? (
                    <WriteComment
                      course={course}
                      semesters={semesterList}
                      instructor={instructor}
                      setUserComment={setUserComment}
                      semestersList={data.sections}
                      reply={reply}
                      setReply={setReply}
                      edit={true}
                    />
                  ) : (
                    <div></div>
                  )}
                </div>
                {/* <div rows={3}>
              <Dropdown name={test}>
                {yum.map((s, i) => (
                  <button key={i} className="btn" onClick={(x) => setTest(x)}>
                    {s}
                  </button>
                ))}
              </Dropdown>
              </div> */}
              </div>

              <div className="list mt-2">
                <div
                  onClick={() => setSelectedSemester(null)}
                  className={selectedSemester === null ? "selected" : ""}
                >
                  Overall
                </div>
                {semesterList.map((sem, i) => (
                  <div
                    key={i}
                    onClick={() => {
                      setPage(1);
                      setSelectedSemester(sem);
                    }}
                    className={selectedSemester === sem ? "selected" : ""}
                  >
                    {sem}
                  </div>
                ))}
              </div>

              <div className="comments mt-2">
                {hasUserComment &&
                  (selectedSemester === userComment.semester ||
                    selectedSemester === null) && (
                    <Comment comment={userComment} isUserComment />
                  )}
                {comments
                  .filter(
                    (c) => !selectedSemester || c.semester === selectedSemester
                  )
                  .filter((c) => c.id !== userComment.id)
                  .map((c) => (
                    <Comment comment={c} setReply={setReply} />
                  ))}
              </div>
            </div>
            <div className="pagination mt-2" style={{ textAlign: "center" }}>
              <button
                className="btn"
                style={{
                  margin: "0 3px",
                  padding: "3px 8px",
                  borderRadius: "4px",
                  backgroundColor: "#5bc0de", // light blue color
                  color: "#fff",
                  cursor: "pointer",
                  transition: "background-color 0.3s, color 0.3s",
                  border: "none",
                }}
                onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                disabled={page === 1}
              >
                <i className="fa fa-chevron-left" />
              </button>
              {Array.from({ length: maxPage }, (_, i) => (
                <button
                  key={i}
                  className={`btn ${page === i + 1 ? "active" : ""}`}
                  style={{
                    margin: "0 3px",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    backgroundColor: page === i + 1 ? "#31b0d5" : "#5bc0de", // darker shade for active
                    color: "#fff",
                    cursor: "pointer",
                    transition: "background-color 0.3s, color 0.3s",
                    border: "none",
                  }}
                  onClick={() => setPage(i + 1)}
                >
                  {i + 1}
                </button>
              ))}
              <button
                className="btn"
                style={{
                  margin: "0 3px",
                  padding: "3px 8px",
                  borderRadius: "4px",
                  backgroundColor: "#5bc0de", // light blue color
                  color: "#fff",
                  cursor: "pointer",
                  transition: "background-color 0.3s, color 0.3s",
                  border: "none",
                }}
                onClick={() => setPage((prev) => Math.min(prev + 1, maxPage))}
                disabled={page === maxPage}
              >
                <i className="fa fa-chevron-right" />
              </button>
            </div>
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
      return <Placeholder type={type} ref={ref} />;
    }

    const [data, setData] = useState({});
    const [columns, setColumns] = useState([]);
    const [filtered, setFiltered] = useState([]);
    const [filterAll, setFilterAll] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const showCol = (info) =>
      REGISTRATION_METRICS_COLUMNS.includes(info) === isCourseEval;

    const generateCol = (info) => {
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
        ),
      };
    };

    useEffect(() => {
      setIsLoading(true);
      if (instructor !== null && course !== null) {
        apiHistory(course, instructor, url_semester)
          .then((res) => {
            console.log("fetching ratings first");

            const sections = Object.values(res.sections);
            const fields = [
              ...new Set(
                sections.reduce((r, s) => [...r, ...Object.keys(s.ratings)], [])
              ),
            ]; // union of all keys of objects in sections
            const ratingCols = orderColumns(fields)
              .map(generateCol)
              .filter((col) => col);
            setData(res);
            setColumns([
              semesterCol,
              nameCol,
              codeCol,
              activityCol,
              formsCol,
              ...ratingCols,
            ]);
          })
          .finally(() => {
            setIsLoading(false);
          });
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [course, instructor, url_semester]);

    const hasData = Boolean(Object.keys(data).length);
    const isCourse = type === "course";

    if (!active) return <></>;

    // Return loading component. TODO: Add spinner/ghost loader.
    if (!hasData && hasSelection && isLoading) {
      return <Loading />;
    }
    // Return placeholder image.
    if (!hasData) {
      return <Placeholder type={type} ref={ref} />;
    }

    const {
      instructor: { name },
      sections,
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
                  forms_returned,
                }) => ({
                  ...ratings,
                  semester: toNormalizedSemester(semester),
                  name,
                  course_code,
                  activity,
                  forms_produced,
                  forms_returned,
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
      <h3 style={{ color: "#b2b2b2", margin: "1.5em", marginBottom: ".5em" }}>
        {type === "course"
          ? "Select an instructor to see individual sections, comments, and more details."
          : "Select a course to see individual sections, comments, and more details."}
      </h3>
    </div>
  );
});

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
