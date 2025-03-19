/* eslint-disable camelcase */
import React from "react";
import styled from "@emotion/styled";
import { lato } from "../../fonts";
import Ratings from "../Infobox/InfoRatings";
import { CourseDescription, CourseHeader } from "../Infobox/CourseInfo";
import { ErrorBox } from "../Infobox/common/ErrorBox";

const InfoBoxCSS = styled.div`
  height: 100%;

  .box {
    font-size: 15px;
    margin: 0px;
    color: #4a4a4a;
  }
  .box {
    padding: 20px;
    background-color: #ffffff;
    /*box-shadow: 0 0 14px 0 rgba(0, 0, 0, 0.07);*/
    margin-bottom: 30px;
  }

  #banner-score {
    margin-bottom: 20px;
  }

  .btn {
    display: inline-block;
    font-weight: 400;
    color: #212529;
    text-align: center;
    vertical-align: middle;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    background-color: transparent;
    border: 1px solid transparent;
    padding: 0.125rem 0.25rem;
    font-size: 1rem;
    line-height: 1;
    border-radius: 0.25rem;
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out,
      border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
  }

  .btn-row {
    display: flex;
    flex-direction: row;
    gap: 0.5rem;
    align-items: center;
    margin: 0.125rem;
  }

  .btn-action {
    background-color: #ccc;
    color: white;
    padding: 0.5rem 0.5rem;
  }

  .btn-action:hover {
    background-color: #84b8ba;
    color: white;
  }

  .btn-action:focus,
  .btn-primary:focus {
    color: white;
  }

  #banner-info .title {
    font-size: 1.5rem;
    letter-spacing: -0.7px;
    margin-bottom: 0px;
    font-weight: 500;
  }

  #banner-info .subtitle {
    font-size: 1.1rem;
    letter-spacing: -0.5px;
    font-weight: normal;
    margin-bottom: 0;
  }

  #banner-info .nowrap {
    white-space: nowrap;
  }

  #banner-info p.desc {
    line-height: 150%;
    margin-bottom: 15px;
    /*font-family: AvenirNext;*/
    font-size: 15px;
    letter-spacing: -0.3px;
  }

  .scorebox.course {
    background-color: #6274f1;
  }

  .scorebox.instructor {
    background-color: #ffc107;
  }

  .scorebox.difficulty {
    background-color: #76bf96;
  }

  .scorebox.workload {
    background-color: #df5d56;
  }

  .scorebox.rating-bad {
    background-color: #ffc107;
  }

  .scorebox.rating-okay {
    background-color: #6274f1;
  }

  .scorebox.rating-good {
    background-color: #76bf96;
  }

  .courseCartRow {
    float: none;
  }

  .scoredesc {
    margin-top: 15px;
    padding-bottom: 4px;
    margin-bottom: 9px;
    border-bottom: 1px solid #dbdbdb;
  }

  .courseCartRow > .scorebox {
    width: 100px;
    height: 100px;
  }

  .courseCartRow > .scorebox > .desc {
    font-size: 15px;
    margin-top: -5px;
    color: white;
  }

  .courseCartRow > .scorebox > .num {
    margin-top: 5px;
    font-size: 3em;
    color: white;
  }

  .scoredesc .title {
    display: inline-block;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.5rem;
    margin-bottom: 0;
  }

  .scoredesc .subtitle {
    display: inline-block;
    font-size: 15px;
    color: #868686;
  }

  .scorebox {
    display: inline-block;
    margin-left: 0.4rem;
    margin-right: 0.4rem;
    height: 3rem;
    width: 3rem;
    border-radius: 4px;
    text-align: center;
    background: rgb(255, 255, 255);
  }

  .scorebox .num {
    color: white;
    margin-top: 0.6rem;
    font-size: 1.25rem;
  }

  .scorebox .desc {
    font-size: 15px;
    letter-spacing: -0.3px;
    font-size: 0.8rem;
    margin-top: 0.8rem;
    font-weight: bold;
  }

  #live {
    font-size: 1.2em;
  }

  #live .badge {
    margin-right: 5px;
    margin-bottom: 5px;
  }

  #live .badge-success {
    background-color: #5cb85c;
  }

  #live .badge-primary {
    background-color: #6274f1;
  }

  #live .badge .count {
    margin-left: 4px;
    padding-left: 4px;
    border-left: 1px solid rgba(0, 0, 0, 0.15);
  }

  .float-right {
    float: right;
  }

  .badge {
    color: white;
    display: inline-block;
    padding: 0.25em 0.4em;
    font-size: 75%;
    font-weight: 700;
    line-height: 1;
    text-align: center;
    white-space: nowrap;
    vertical-align: baseline;
    border-radius: 0.25rem;
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out,
      border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
  }

  .badge-info {
    background-color: #17a2b8;
  }

  .badge-danger {
    background-color: #dc3545;
  }

  .badge-secondary {
    background-color: #6c757d;
  }
`;

const ErrorWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  flex-direction: column;
`;

/**
 * Information box on the left most side, containing scores and descriptions
 * of course or professor.
 */

//
const InfoBox = ({
  data: {
    course_quality,
    instructor_quality,
    difficulty,
    work_required,
    id: code,
    crosslistings: aliases,
    description,
    title: name,
    notes,
    num_sections: numSections,
  },
  data,
  close,
}) => {
  const hasReviews = !!(
    instructor_quality ||
    course_quality ||
    difficulty ||
    work_required
  );

  if (!data) {
    return <h1>Loading data...</h1>;
  }


  return (
    <InfoBoxCSS className={lato.className}>
      {code ? (
        <div className="box">
          <div id="banner-info" data-type="course">
            <CourseHeader
              close={close}
              aliases={aliases}
              code={code}
              data={data}
              name={name}
              notes={notes}
            />
          </div>
          {hasReviews && (
            <div id="banner-score">
              <Ratings
                value="Average"
                instructor={instructor_quality}
                course={course_quality}
                difficulty={difficulty}
                work={work_required}
              />
            </div>
          )}
          <CourseDescription description={description} />
        </div>
      ) : (
        <ErrorWrapper>
          <ErrorBox style={{ marginTop: "auto", marginBottom: "auto" }}>
            Course not found
          </ErrorBox>
        </ErrorWrapper>
      )}
    </InfoBoxCSS>
  );
};

export default InfoBox;
