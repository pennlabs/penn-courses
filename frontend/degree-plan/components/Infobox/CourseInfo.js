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

const linkCourseCodes = (text) =>
  reactStringReplace(text, /([A-Z]{2,4}[ -]\d{3,4})/g, (m, i) => (
    <a
      href={`https://penncoursereview.com/course/${m.replace(" ", "-")}`}
      key={m + i}
    >
      {m}
    </a>
  ));

export const CourseDescription = ({ description }) => (
  <p className="desc">{linkCourseCodes(description)}</p>
);

const MAX_LISTED_COURSES = 8;

const CourseCodeList = ({ codes }) => {
  const shown = codes.slice(0, MAX_LISTED_COURSES);
  const hidden = codes.length - shown.length;
  return (
    <>
      {shown.map((code, i) => [
        i > 0 && <div key={`${code}-sep`}>&#44;&nbsp;</div>,
        <a href={`https://penncoursereview.com/course/${code}`} key={code}>
          {code}
        </a>,
      ])}
      {hidden > 0 && <div>&nbsp;and {hidden} more</div>}
    </>
  );
};

const CourseLink = ({ code }) => (
  <a href={`https://penncoursereview.com/course/${code}`}>
    {code.replace("-", " ")}
  </a>
);

/** A prerequisite rule inline, e.g. "CIS 1200 and (CIS 1600 or MATH 1400)", with links. */
const PrereqRuleText = ({ rule, nested = false }) => {
  if (typeof rule === "string") return <CourseLink code={rule} />;
  if ("text" in rule) return <span>{rule.text}</span>;
  const [op, children] = "and" in rule ? ["and", rule.and] : ["or", rule.or];
  return (
    <span>
      {nested && "("}
      {children.map((child, i) => (
        <React.Fragment key={i}>
          {i > 0 && ` ${op} `}
          <PrereqRuleText rule={child} nested />
        </React.Fragment>
      ))}
      {nested && ")"}
    </span>
  );
};

const ChainList = styled.ul`
  list-style: none;
  margin: 0.25rem 0 0.25rem 0;
  padding-left: 1rem;
  border-left: 1px solid #dbdbdb;
  font-size: 0.85rem;
  color: #4a4a4a;
`;

const ChainToggle = styled.button`
  border: none;
  background: none;
  padding: 0;
  color: #3273dc;
  cursor: pointer;
  font-size: 0.85rem;
`;

/**
 * One node of the prerequisite chain: a course (expanded into its own prerequisites unless it
 * already appears above it), a condition that isn't a course, or all / one of several.
 */
const PrereqChainNode = ({ rule, chain, path }) => {
  if (typeof rule === "string") {
    const entry = chain[rule];
    const expand = entry?.prerequisite_rule && !path.includes(rule);
    return (
      <li>
        <CourseLink code={rule} />
        {entry?.title && <span> {entry.title}</span>}
        {expand && (
          <ChainList>
            <PrereqChainNode
              rule={entry.prerequisite_rule}
              chain={chain}
              path={[...path, rule]}
            />
          </ChainList>
        )}
      </li>
    );
  }
  if ("text" in rule) {
    return (
      <li>
        <em>{rule.text}</em>
      </li>
    );
  }
  const [label, children] =
    "and" in rule ? ["All of:", rule.and] : ["One of:", rule.or];
  return (
    <li>
      {label}
      <ChainList>
        {children.map((child, i) => (
          <PrereqChainNode key={i} rule={child} chain={chain} path={path} />
        ))}
      </ChainList>
    </li>
  );
};

/**
 * Prerequisite information for a course. Prefers the required prerequisites parsed from
 * Path@Penn (`prerequisite_chain`), then the structured links (`prerequisite_courses`), then
 * the registrar's free text, so a course never shows less than the text field already
 * offered. When the prerequisites have prerequisites of their own, the whole chain can be
 * expanded. `dependent_courses` are the courses this one unlocks.
 */
export const CoursePrerequisites = ({
  code,
  prerequisites,
  prerequisiteCourses,
  prerequisiteChain,
  dependentCourses,
}) => {
  const [showChain, setShowChain] = React.useState(false);
  const chain = prerequisiteChain ?? {};
  const rule = chain[code]?.prerequisite_rule;
  const hasChain = Object.entries(chain).some(
    ([other, entry]) => other !== code && entry.prerequisite_rule
  );
  const structured = prerequisiteCourses ?? [];
  const dependents = dependentCourses ?? [];
  const text = (prerequisites ?? "").trim();
  if (!rule && !structured.length && !text && !dependents.length) {
    return null;
  }
  return (
    <div className="prereqs">
      {(rule || structured.length > 0 || text) && (
        <CourseCodeQualifier>
          <strong>Prerequisites:&nbsp;</strong>
          {rule ? (
            <PrereqRuleText rule={rule} />
          ) : structured.length > 0 ? (
            <CourseCodeList codes={structured} />
          ) : (
            <span>{linkCourseCodes(text)}</span>
          )}
        </CourseCodeQualifier>
      )}
      {rule && hasChain && (
        <div>
          <ChainToggle onClick={() => setShowChain(!showChain)}>
            {showChain ? "Hide prerequisite chain" : "Show prerequisite chain"}
          </ChainToggle>
          {showChain && (
            <ChainList>
              <PrereqChainNode rule={rule} chain={chain} path={[code]} />
            </ChainList>
          )}
        </div>
      )}
      {dependents.length > 0 && (
        <CourseCodeQualifier>
          <strong>Unlocks:&nbsp;</strong>
          <CourseCodeList codes={dependents} />
        </CourseCodeQualifier>
      )}
    </div>
  );
};
