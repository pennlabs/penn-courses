import React, { useEffect, useState } from "react";

import Ratings from "./InfoRatings";
import { CourseDescription, CourseHeader } from "./CourseInfo";
import InstructorInfo from "./InstructorInfo";
import { DepartmentHeader, DepartmentGraphs } from "./DepartmentInfo";
import { apiContact } from "../../utils/api";

import styled from "styled-components";

const NewLabel = styled.div`
  background: #ea5a48;
  color: #fff;
  border-radius: 0.875rem;
  font-size: 0.5625rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  padding: 0.1875rem 0.375rem;
  text-align: center;
  align-self: center;
  margin-right: 10px;
  justify-self: start;
`;

const StatsToggleContainer = styled.div`
  display: flex;
  justify-content: start;
  margin: 20px 0px;
  flex-direction: row;
`;

/**
 * Information box on the left most side, containing scores and descriptions
 * of course or professor.
 */

const InfoBox = ({
  type,
  semester,
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
  selectedCourses,
  isCourseEval,
  setIsCourseEval
}) => {
  const [contact, setContact] = useState(null);
  const [inCourseCart, setInCourseCart] = useState(
    Boolean(localStorage.getItem(code))
  );
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

  const isCourse = type === "course";
  const isInstructor = type === "instructor";
  const isDepartment = type === "department";

  useEffect(() => {
    if (isInstructor) apiContact(name).then(setContact);
  }, [name, isInstructor]);

  const handleCartAdd = key => {
    let instructor = "Average Professor";
    if (key !== "average") {
      ({
        name: instructor,
        average_reviews: average,
        recent_reviews: recent
      } = instructors[key]);
    }
    const info = Object.keys(average).map(category => ({
      category,
      average: average[category],
      recent: recent[category]
    }));
    const item = JSON.stringify({
      version: 1,
      course: code,
      instructor,
      info
    });
    localStorage.setItem(code, item);
    if (window.onCartUpdated) window.onCartUpdated();
    setInCourseCart(true);
  };
  const handleCartRemove = () => {
    localStorage.removeItem(code);
    setInCourseCart(false);
    if (window.onCartUpdated) window.onCartUpdated();
  };

  if (!data) {
    return <h1>Loading data...</h1>;
  }

  return (
    <div className="box">
      <div id="banner-info" data-type="course">
        {isCourse && (
          <CourseHeader
            aliases={aliases}
            code={code}
            semester={semester}
            data={data}
            name={name}
            notes={notes}
            instructors={instructors}
            type={type}
            inCourseCart={inCourseCart}
            handleAdd={handleCartAdd}
            handleRemove={handleCartRemove}
            liveData={liveData}
          />
        )}

        {isInstructor && (
          <InstructorInfo name={name} contact={contact} notes={notes} />
        )}

        {isDepartment && <DepartmentHeader name={name} code={code} />}
      </div>

      {data.registration_metrics && (
        <StatsToggleContainer>
          <NewLabel>NEW</NewLabel>
          <div className="btn-group">
            <button
              onClick={() => setIsCourseEval(false)}
              className={`btn btn-sm ${
                isCourseEval ? "btn-sub-secondary" : "btn-sub-primary"
              }`}
            >
              Student Evaluations
            </button>
            <button
              onClick={() => setIsCourseEval(true)}
              className={`btn btn-sm ${
                isCourseEval ? "btn-sub-primary" : "btn-sub-secondary"
              }`}
            >
              Registration Metrics
            </button>
          </div>
        </StatsToggleContainer>
      )}

      {!isDepartment && hasReviews && (
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

      {isDepartment && (
        <DepartmentGraphs
          courses={selectedCourses}
          isCourseEval={isCourseEval}
        />
      )}

      {isCourse && <CourseDescription description={description} />}
    </div>
  );
};

export default InfoBox;
