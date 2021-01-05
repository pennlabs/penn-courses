import React, { useMemo } from "react";
import reactStringReplace from "react-string-replace";
import { Link } from "react-router-dom";

import { CourseDetails, Popover, PopoverTitle } from "../common";
import {
  convertInstructorName,
  convertSemesterToInt,
  toNormalizedSemester
} from "../../utils/helpers";
import { act } from "react-dom/test-utils";

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

const activityMap = {
  REC: "Recitation",
  LEC: "Lecture",
  SEM: "Seminar",
  LAB: "Laboratory"
};
const laterSemester = (a, b) => {
  if (!a.localeCompare) {
    return b;
  } else if (!b.localeCompare) {
    return a;
  }

  if (a.localeCompare(b) > 0) {
    return a;
  } else {
    return b;
  }
};
const TagsNotOffered = ({ data }) => {
  const { instructors: instructorData = {}, code = "" } = data;
  const courseName = code.replace("-", " ");
  let mostRecent = Object.values(instructorData)
    .map(a => a.latest_semester)
    .reduce(laterSemester);

  if (!mostRecent) {
    return <div />;
  }
  mostRecent = toNormalizedSemester(mostRecent);
  return (
    <div>
      <div id="live">
        <PopoverTitle
          title={
            <span>
              {courseName} was last taught in <b>{mostRecent}</b>.
            </span>
          }
        >
          <span className="badge badge-secondary">{mostRecent}</span>
        </PopoverTitle>
      </div>
    </div>
  );
};
const TagsWhenOffered = ({
  liveData = null,
  data = {},
  existingInstructors
}) => {
  const { instructors: instructorData = {}, code = "" } = data;
  const courseName = code.replace("-", " ");
  // TODO: Get syllabus data
  // const [syllabi, prereqs] = useMemo(
  //   () => [getSyllabusData(courses), getPrereqData(courses)],
  //   [courses]
  // );
  const { sections, semester } = liveData;
  const term = toNormalizedSemester(semester);
  const credits =
    sections.length > 0
      ? sections.map(({ credits }) => credits).reduce((a, b) => Math.max(a, b))
      : null;

  const activityTypes = [...new Set(sections.map(({ activity }) => activity))];
  const sectionsByActivity = {};
  activityTypes.forEach(activity => {
    sectionsByActivity[activity] = sections.filter(
      ({ activity: sectionActivity }) => activity === sectionActivity
    );
  });
  const oldInstructors = Object.values(instructorData).map(({ name }) => name);
  const newInstructors = sections
    .flatMap(({ instructors }) => instructors)
    .filter(inst => oldInstructors.indexOf(inst) === -1);

  const syllabi = [];
  const courses = [];
  const prereqs = [];
  const links = [];

  return (
    <div>
      <div id="live">
        <PopoverTitle
          title={
            <span>
              {courseName} will be taught in <b>{term}</b>.
            </span>
          }
        >
          <span className="badge badge-info">{term}</span>
        </PopoverTitle>
        {credits && (
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

        {Object.entries(sectionsByActivity).map(([activity, sections], i) => {
          const openSections = sections.filter(({ status }) => status === "O");
          return (
            <PopoverTitle
              key={i}
              title={
                <span>
                  <b>{openSections.length}</b> out of <b>{sections.length}</b>{" "}
                  sections are open for {courseName}.
                  <ul style={{ marginBottom: 0 }}>
                    {sections.map(data => (
                      <CourseDetails key={data.id} data={data} />
                    ))}
                  </ul>
                </span>
              }
            >
              <span
                className={`badge ${
                  openSections.length ? "badge-success" : "badge-danger"
                }`}
              >
                {activityMap[activity] || ""}
                <span className="count">
                  {openSections.length}/{sections.length}
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
      {Boolean(newInstructors.length) && (
        <div>
          New Instructors:{" "}
          {newInstructors
            .sort()
            .filter((elt, idx, arr) => elt.id !== arr[idx - 1].id)
            .map((item, idx) => (
              <span key={item.id}>
                {idx > 0 && ", "}
                <Link to={`/instructor/${item.id}`}>{item.name}</Link>}
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
    {liveData && liveData.sections && liveData.sections.length > 0 ? (
      <TagsWhenOffered
        liveData={liveData}
        data={data}
        existingInstructors={Object.values(instructors).map(a => a.name)}
      />
    ) : (
      <TagsNotOffered data={data} />
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
