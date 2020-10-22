import React, { useMemo } from "react";
import reactStringReplace from "react-string-replace";
import { Link } from "react-router-dom";

import { CourseDetails, Popover, PopoverTitle } from "../common";
import {
  convertInstructorName,
  convertSemesterToInt
} from "../../utils/helpers";

const getSyllabusData = courses =>
  Object.values(courses)
    .map(course =>
      Object.values(course)
        .filter(({ syllabus_url: url }) => url)
        .map(
          ({
            syllabus_url: url,
            section_id_normalized: sectionId,
            instructors = []
          }) => {
            const instructedBy =
              instructors.map(c => c.name).join(", ") || "Unknown";
            return {
              url,
              name: `${sectionId} - ${instructedBy}`
            };
          }
        )
    )
    .flat()
    .sort((a, b) => a.name.localeCompare(b.name));

const getPrereqData = courses => {
  const prereqString = Object.values(courses)
    .map(a =>
      Object.values(a)
        .map(({ prerequisite_notes: notes = [] }) => notes.join(" "))
        .filter(b => b)
    )
    .flat()
    .join(" ");
  const prereqs = [
    ...new Set(prereqString.match(/[A-Z]{2,4}[ -]\d{3}/g))
  ].map(a => a.replace(" ", "-"));
  return prereqs;
};

const Tags = ({
  data = {},
  courses = {},
  credits,
  existingInstructors,
  instructors,
  instructor_links: links,
  term
}) => {
  const { instructors: instructorData = {}, code = "" } = data;
  const courseName = code.replace("-", " ");
  const [syllabi, prereqs] = useMemo(
    () => [getSyllabusData(courses), getPrereqData(courses)],
    [courses]
  );
  const newInstructors = useMemo(() => {
    const existingFilter = existingInstructors.map(convertInstructorName);
    const newInstructors = {};
    if (instructors) {
      instructors.forEach(instructor => {
        const key = convertInstructorName(instructor);
        newInstructors[key] = instructor;
      });
    }
    existingFilter.forEach(i => {
      delete newInstructors[i];
    });
    return newInstructors;
  }, [existingInstructors, instructors]);

  const isTaught = Boolean(Object.values(courses).length);
  const mostRecent = useMemo(() => {
    if (!isTaught) {
      const semesterTaught = Math.max(
        ...Object.values(instructorData)
          .map(a => a.most_recent_semester)
          .filter(a => typeof a !== "undefined")
          .map(convertSemesterToInt)
      );
      if (semesterTaught > 0) {
        return `${
          ["Spring", "Summer", "Fall"][semesterTaught % 3]
        } ${Math.floor(semesterTaught / 3)}`;
      }
    }
    return null;
  }, [isTaught, instructorData]);

  return (
    <div>
      <div id="live">
        {isTaught ? (
          <PopoverTitle
            title={
              <span>
                {courseName} will be taught in <b>{term}</b>.
              </span>
            }
          >
            <span className="badge badge-info">{term}</span>
          </PopoverTitle>
        ) : (
          <PopoverTitle
            title={
              <span>
                {courseName} was last taught in <b>{mostRecent}</b>.
              </span>
            }
          >
            <span className="badge badge-secondary">{mostRecent}</span>
          </PopoverTitle>
        )}
        {isTaught && (
          <PopoverTitle
            title={
              <span>
                {courseName} is <b>{credits}</b> credit unit
                {credits === 1 ? "" : "s"}
              </span>
            }
          >
            <span className="badge badge-primary">{credits} CU</span>
          </PopoverTitle>
        )}
        {Object.values(courses).map((info, i) => {
          if (!info.length) {
            return null;
          }
          const [{ activity_description: desc }] = info;
          const open = info.filter(a => !a.is_closed && !a.is_cancelled);
          return (
            <PopoverTitle
              key={i}
              title={
                <span>
                  <b>{open.length}</b> out of <b>{info.length}</b>{" "}
                  {desc.toLowerCase()} sections are open for {courseName}.
                  <ul style={{ marginBottom: 0 }}>
                    {info
                      .sort((x, y) =>
                        x.section_id_normalized.localeCompare(
                          y.section_id_normalized
                        )
                      )
                      .map(data => (
                        <CourseDetails
                          key={data.section_id_normalized}
                          data={data}
                        />
                      ))}
                  </ul>
                </span>
              }
            >
              <span
                className={`badge ${
                  open.length ? "badge-success" : "badge-danger"
                }`}
              >
                {desc}
                <span className="count">
                  {open.length}/{info.length}
                </span>
              </span>
            </PopoverTitle>
          );
        })}
        {Boolean(syllabi.length) && (
          <Popover
            button={
              <span className="badge badge-secondary">
                {syllabi.length} {syllabi.length !== 1 ? "Syllabi" : "Syllabus"}
              </span>
            }
          >
            {syllabi.map((a, i) => (
              <div key={i}>
                <a target="_blank" rel="noopener noreferrer" href={a.url}>
                  {a.name}
                </a>
              </div>
            ))}
          </Popover>
        )}
      </div>
      {Boolean(prereqs.length) && (
        <div className="prereqs">
          Prerequisites:{" "}
          {prereqs.map((a, i) => [
            i > 0 && ", ",
            <span key={i}>
              <Link to={`/course/${a}`}>{a.replace("-", " ")}</Link>
            </span>
          ])}
        </div>
      )}
      {Boolean(Object.keys(newInstructors).length) && (
        <div>
          New Instructors:
          {Object.values(newInstructors)
            .sort()
            .map((item, i) => (
              <span key={i}>
                {i > 0 && ", "}
                {links[item] ? (
                  <Link to={`/instructor/${links[item]}`}>{item}</Link>
                ) : (
                  item
                )}
              </span>
            ))}
        </div>
      )}
    </div>
  );
};

export const CourseHeader = ({
  aliases,
  code,
  inCourseCart,
  instructors,
  name,
  notes,
  handleAdd,
  handleRemove,
  liveData,
  data
}) => (
  <div className="course">
    <div className="title">
      {code.replace("-", " ")}

      <span className="float-right">
        {inCourseCart ? (
          <span
            onClick={handleRemove}
            className="courseCart btn btn-action"
            title="Remove from Cart"
          >
            <i className="fa fa-fw fa-trash-alt" />
          </span>
        ) : (
          <Popover
            button={
              <span className="courseCart btn btn-action" title="Add to Cart">
                <i className="fa fa-fw fa-cart-plus" />
              </span>
            }
          >
            <div className="popover-title">Add to Cart</div>
            <div
              className="popover-content"
              style={{ maxHeight: 400, overflowY: "auto" }}
            >
              <div id="divList">
                <ul className="professorList">
                  <li>
                    <button onClick={() => handleAdd("average")}>
                      Average Professor
                    </button>
                  </li>
                  {Object.keys(instructors)
                    .sort((a, b) =>
                      instructors[a].name.localeCompare(instructors[b].name)
                    )
                    .map(key => (
                      <li key={key}>
                        <button onClick={() => handleAdd(key)}>
                          {instructors[key].name}
                        </button>
                      </li>
                    ))}
                </ul>
              </div>
            </div>
          </Popover>
        )}{" "}
        <a
          target="_blank"
          rel="noopener noreferrer"
          title="Get Alerted"
          href={`https://penncoursealert.com/?course=${code}&source=pcr`}
          className="btn btn-action"
        >
          <i className="fas fa-fw fa-bell" />
        </a>
      </span>
    </div>
    {aliases && Boolean(aliases.length) && (
      <div className="crosslist">
        Also:{" "}
        {aliases.map((cls, i) => [
          i > 0 && ", ",
          <Link key={cls} to={`/course/${cls}`}>
            {cls}
          </Link>
        ])}
      </div>
    )}
    <p className="subtitle">{name}</p>
    {notes &&
      notes.map(note => (
        <div key={note} className="note">
          <i className="fa fa-thumbtack" /> {note}
        </div>
      ))}
    {liveData && (
      <Tags
        {...liveData}
        data={data}
        existingInstructors={Object.values(instructors).map(a => a.name)}
      />
    )}
  </div>
);

export const CourseDescription = ({ description }) => {
  const content = reactStringReplace(
    description,
    /([A-Z]{2,4}[ -]\d{3})/g,
    (m, i) => (
      <Link to={`/course/${m.replace(" ", "-")}`} key={m + i}>
        {m}
      </Link>
    )
  );
  return <p className="desc">{content}</p>;
};
