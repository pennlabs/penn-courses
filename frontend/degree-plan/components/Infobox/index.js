import React, { useState } from "react";
import styled from "styled-components";
import { lato } from "@/fonts";
import Ratings from "./InfoRatings";
import { CourseDescription, CourseHeader } from "./CourseInfo";


const InfoBoxCSS = styled.div`
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
    padding: .375rem .75rem;
    font-size: 1rem;
    line-height: 1.5;
    border-radius: .25rem;
    transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
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
    font-size: 30px;
    letter-spacing: -0.7px;
    margin-bottom: 0px;
    font-weight: 500;
}

#banner-info .subtitle {
    font-size: 20px;
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

.courseCartRow>.scorebox {
    width: 100px;
    height: 100px;
}

.courseCartRow>.scorebox>.desc {
    font-size: 15px;
    margin-top: -5px;
    color: white;
}

.courseCartRow>.scorebox>.num {
    margin-top: 5px;
    font-size: 3em;
    color: white;
}

.scoredesc .title {
    display: inline-block;
    font-size: 17px;
}

.scoredesc .subtitle {
    display: inline-block;
    font-size: 15px;
    color: #868686;
}

.scorebox {
    display: inline-block;
    margin-left: 5px;
    margin-right: 5px;
    height: 70px;
    width: 70px;
    border-radius: 4px;
    text-align: center;
    background: rgb(255, 255, 255);
}

.scorebox .num {
    color: white;
    margin-top: 16px;
    font-size: 25px;
}

.scorebox .desc {
    font-size: 15px;
    letter-spacing: -0.3px;
    margin-top: 20px;
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
    padding: .25em .4em;
    font-size: 75%;
    font-weight: 700;
    line-height: 1;
    text-align: center;
    white-space: nowrap;
    vertical-align: baseline;
    border-radius: .25rem;
    transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
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
`

/**
 * Information box on the left most side, containing scores and descriptions
 * of course or professor.
 */

const InfoBox = ({
  data: {
    average_reviews: average = {},
    recent_reviews: recent = {},
    code = "",
    aliases,
    description,
    instructors,
    name,
    notes,
    num_sections: numSections,
    num_sections_recent: numSectionsRecent
  },
  data,
  liveData,
  close
}) => {
  const {
    rInstructorQuality: avgInstructorQuality,
    rCourseQuality: avgCourseQuality,
    rDifficulty: avgDifficulty,
    rWorkRequired: avgWorkRequired
  } = average;
  const {
    rInstructorQuality: recentInstructorQuality,
    rCourseQuality: recentCourseQuality,
    rDifficulty: recentDifficulty,
    rWorkRequired: recentWorkRequired
  } = recent;
  const hasReviews =
    avgInstructorQuality != null ||
    avgCourseQuality != null ||
    avgDifficulty != null ||
    avgWorkRequired != null;

  if (!data) {
    return <h1>Loading data...</h1>;
  }

  return (
    <InfoBoxCSS className={lato.className}>
      <div className="box">
        <div id="banner-info" data-type="course">
          <CourseHeader
            close={close}
            aliases={aliases}
            code={code}
            data={data}
            name={name}
            notes={notes}
            instructors={instructors}
            liveData={liveData}
          />
        </div>

        {hasReviews && (
          <div id="banner-score">
            <Ratings
              value="Average"
              instructor={avgInstructorQuality}
              course={avgCourseQuality}
              difficulty={avgDifficulty}
              work={avgWorkRequired}
              num_sections={numSections}
            />

            <Ratings
              value="Recent"
              instructor={recentInstructorQuality}
              course={recentCourseQuality}
              difficulty={recentDifficulty}
              work={recentWorkRequired}
              num_sections={numSectionsRecent}
            />
          </div>
        )}
        <CourseDescription description={description} />
      </div>
    </InfoBoxCSS>
  );
};

export default InfoBox;
