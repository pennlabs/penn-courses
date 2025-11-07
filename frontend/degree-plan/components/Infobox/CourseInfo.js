import React from "react";
import reactStringReplace from "react-string-replace";
import styled from "@emotion/styled";

import * as ReactTooltip from "react-tooltip";
import { toNormalizedSemester } from "./util/helpers";

const TagsNotOffered = ({ data }) => {
  let { semester: mostRecent } = data;
  if (!mostRecent) {
    return <div />;
  }
  mostRecent = toNormalizedSemester(mostRecent);
  return (
    <div id="live">
      <span className="badge badge-success">{mostRecent}</span>
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

const PCRLink = styled.a`
  float: right;
  font-size: 0.5rem;
`;

export const CourseHeader = ({ close, aliases, code, name, notes, data }) => (
  <div className="course">
    <div className="title">
      {code.replace("-", " ")}

      <PCRLink
        target="_blank"
        rel="noopener noreferrer"
        title="View in Penn Course Review"
        href={`https://penncoursereview.com/course/${code}/`}
        className="btn btn-action btn-row"
      >
        <i className="fas fa-link fa-xs" />
        <div>view in PCR</div>
      </PCRLink>
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
              marginBottom: "0.3rem",
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
          <a
            href={`https://penncoursereview.com/course/${cls}/${data.latest_semester}`}
            key={`${cls}/${data.latest_semester}`}
          >
            {cls}
          </a>,
        ])}
      </CourseCodeQualifier>
    )}

    {
      // eslint-disable-next-line camelcase
      !!data?.historical_codes?.length && (
        <CourseCodeQualifier>
          <strong>Previously:&nbsp;</strong>
          {data.historical_codes.map((obj, i) => [
            i > 0 && <div>&#44;&nbsp;</div>,
            obj.branched_from ? (
              <a
                href={`https://penncoursereview.com/course/${obj.full_code}/${obj.semester}`}
              >
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
            ),
          ])}
          &nbsp;
          <span data-tip data-for="historical-tooltip">
            <i
              className="fa fa-question-circle"
              style={{
                color: "#c6c6c6",
                fontSize: "13px",
                marginBottom: "0.3rem",
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
      )
    }
    <p className="subtitle">{name}</p>
    {notes &&
      notes.map((note) => (
        <div key={note} className="note">
          <i className="fa fa-thumbtack" /> {note}
        </div>
      ))}
    <TagsNotOffered data={data} />
  </div>
);

export const CourseDescription = ({ description }) => {
  const content = reactStringReplace(
    description,
    /([A-Z]{2,4}[ -]\d{3,4})/g,
    (m, i) => (
      <a
        href={`https://penncoursereview.com/course/${m.replace(" ", "-")}`}
        key={m + i}
      >
        {m}
      </a>
    )
  );
  return <p className="desc">{content}</p>;
};
