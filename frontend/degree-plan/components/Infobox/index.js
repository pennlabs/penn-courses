import React, { useState } from "react";

import Ratings from "./InfoRatings";
import { CourseDescription, CourseHeader } from "./CourseInfo";

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
    <div className="box">
      <div id="banner-info" data-type="course">
        <CourseHeader
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
  );
};

export default InfoBox;
