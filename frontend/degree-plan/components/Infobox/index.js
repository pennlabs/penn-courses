import React, { useState } from "react";

import Ratings from "./InfoRatings";
import { CourseDescription, CourseHeader } from "./CourseInfo";

import styled from "styled-components";

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
}) => {
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
  );
};

export default InfoBox;
