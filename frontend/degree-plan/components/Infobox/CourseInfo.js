import React from "react";
import reactStringReplace from "react-string-replace";
import { GrayIcon } from '@/components/common/bulma_derived_components';
import styled from '@emotion/styled'

import { CourseDetails } from "./common/CourseDetails";
import { Popover, PopoverTitle } from "./common/Popover";
import { toNormalizedSemester } from "./util/helpers";

import ReactTooltip from "react-tooltip";

const activityMap = {
  REC: "Recitation",
  LEC: "Lecture",
  SEM: "Seminar",
  LAB: "Laboratory"
};

const CloseIcon = styled(GrayIcon)`
  pointer-events: auto;
  margin-left: 0.5rem;

  & :hover {
    color: #707070;
  }
`

const TagsNotOffered = ({ data }) => {
  let {
    latest_semester: mostRecent,
    code = ""
  } = data;
  const courseName = code.replace("-", " ");
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
}) => {
  const { instructors: instructorData = {}, code = "" } = data;
  const courseName = code.replace("-", " ");
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
  const oldInstructorIds = new Set(
    Object.values(instructorData).map(({ id }) => id)
  );
  const seenNewInstructorIds = new Set();
  const newInstructors = sections
    .filter(section => section.activity !== "REC")
    .flatMap(({ instructors }) => instructors)
    .filter(({ id }) => {
      if (oldInstructorIds.has(id) || seenNewInstructorIds.has(id)) {
        return false;
      }
      seenNewInstructorIds.add(id);
      return true;
    });

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
              <a href={`https://penncoursereview.com/course/${a}`}>{a.replace("-", " ")}</a>
            </span>
          ])}
        </div>
      )}
      {Boolean(newInstructors.length) && (
        <div>
          New Instructors:{" "}
          {newInstructors
            .sort()
            .filter(
              (elt, idx, arr) =>
                arr[idx - 1] === undefined || elt.id !== arr[idx - 1].id
            )
            .map((item, idx) => (
              <span key={item.id}>
                {idx > 0 && ", "}
                <a href={`https://penncoursereview.com/instructor/${item.id}`}>{item.name}</a>
              </span>
            ))}
        </div>
      )}
    </div>
  );
};

const CourseCodeQualifier = styled.div`
  display: flex;
  flex-direction: row;
  color: #4a4a4a;
  align-items: center;
  flex-wrap: wrap;
`;

const Actions = styled.div`
  display: inline-flex;
  justify-content: center;
  align-items: center;
  float: right;
  gap: 0.5rem;
`

const PCRLogo = styled.img`
  height: 2.5rem;
  display: block;
`;

const Spacer = styled.div`
  height: 0.6rem;
`;

export const CourseHeader = ({
  close,
  aliases,
  code,
  name,
  notes,
  liveData,
  data,
}) => (
  <div className="course">
    <div className="title">
      {code.replace("-", " ")}

      <Actions>
        {!data?.last_offered_sem_if_superceded && (
          <a
            target="_blank"
            rel="noopener noreferrer"
            title="Get Alerted"
            href={`https://penncoursealert.com/?course=${code}&source=pcr`}
            className="btn btn-action"
          >
            <i className="fas fa-fw fa-bell" />
          </a>
        )}
        <a
          target="_blank"
          rel="noopener noreferrer"
          title="View in Penn Course Review"
          href={`https://penncoursereview.com/course/${code}/`}
        >
          <PCRLogo src="/images/pcr-logo.png" />
        </a>
        <CloseIcon onClick={close}>
          <i className="fas fa-times fa-md"></i>
      </CloseIcon>
      </Actions>
    </div>
    {data.last_offered_sem_if_superceded && (
      <CourseCodeQualifier>
        <a href={`https://penncoursereview.com/course/${code}`}>Superseded</a>
        &nbsp;
        <span data-tip data-for="superseded-tooltip">
          <i
            className="fa fa-question-circle"
            style={{
              color: "#c6c6c6",
              fontSize: "13px",
              marginBottom: "0.3rem"
            }}
          />
        </span>
        <ReactTooltip
          id="superseded-tooltip"
          place="right"
          className="opaque"
          type="light"
          effect="solid"
          border={true}
          borderColor="#ededed"
          textColor="#4a4a4a"
        >
          <span className="tooltip-text">
            This course was last offered in{" "}
            {toNormalizedSemester(data.last_offered_sem_if_superceded)}.
            <br />
            It has more recently been superseeded by another course
            <br />
            with the same full code. Click to visit the most recent
            <br />
            course with this full code.
          </span>
        </ReactTooltip>
      </CourseCodeQualifier>
    )}
    {data.last_offered_sem_if_superceded && (
      <CourseCodeQualifier>
        <strong>Last offered:&nbsp;</strong>
        {toNormalizedSemester(data.last_offered_sem_if_superceded)}
      </CourseCodeQualifier>
    )}
    {!!aliases?.length && (
      <CourseCodeQualifier>
        <strong>Also:&nbsp;</strong>
        {aliases.map((cls, i) => [
          i > 0 && <div>&#44;&nbsp;</div>,
          <a href={`https://penncoursereview.com/course/${cls}/${data.latest_semester}`} key={i}>
            {cls}
          </a>
        ])}
      </CourseCodeQualifier>
    )}
    {!!data?.historical_codes?.length && (
      <CourseCodeQualifier>
        <strong>Previously:&nbsp;</strong>
        {data.historical_codes.map((obj, i) => [
          i > 0 && <div>&#44;&nbsp;</div>,
          obj.branched_from ? (
            <a href={`https://penncoursereview.com/course/${obj.full_code}/${obj.semester}`}>
              {obj.full_code}
              {data.historical_codes.some(
                (other, otherI) =>
                  other.full_code === obj.full_code && i !== otherI
              )
                ? ` (${toNormalizedSemester(obj.semester)})`
                : ""}
            </a>
          ) : (
            <div>{obj.full_code}</div>
          )
        ])}
        &nbsp;
        <span data-tip data-for="historical-tooltip">
          <i
            className="fa fa-question-circle"
            style={{
              color: "#c6c6c6",
              fontSize: "13px",
              marginBottom: "0.3rem"
            }}
          />
        </span>
        <ReactTooltip
          id="historical-tooltip"
          place="right"
          className="opaque"
          type="light"
          effect="solid"
          border={true}
          borderColor="#ededed"
          textColor="#4a4a4a"
        >
          <span className="tooltip-text">
            Historical courses are grouped on PCR <br />
            using a variety of approximate methods.
            <br />
            Grouped courses should not necessarily
            <br />
            be seen as equivalent for the purposes of
            <br />
            academic planning or fulfilling requirements.
          </span>
        </ReactTooltip>
      </CourseCodeQualifier>
    )}
    <Spacer />
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
      />
    ) : (
      <TagsNotOffered data={data} />
    )}
  </div>
);

export const CourseDescription = ({ description }) => {
  const content = reactStringReplace(
    description,
    /([A-Z]{2,4}[ -]\d{3,4})/g,
    (m, i) => (
      <a href={`https://penncoursereview.com/course/${m.replace(" ", "-")}`} key={m + i}>
        {m}
      </a>
    )
  );
  return <p className="desc">{content}</p>;
};
