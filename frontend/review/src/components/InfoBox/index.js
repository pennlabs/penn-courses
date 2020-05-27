import React, { useEffect, useState } from 'react'

import Ratings from './InfoRatings'
import { CourseDescription, CourseHeader } from './CourseInfo'
import InstructorInfo from './InstructorInfo'
import { DepartmentHeader, DepartmentGraphs } from './DepartmentInfo'
import { apiContact } from '../../utils/api'

/**
 * Information box on the left most side, containing scores and descriptions
 * of course or professor.
 */

const InfoBox = ({
  type,
  data: {
    average_ratings: average = {},
    recent_ratings: recent = {},
    code = '',
    aliases,
    description,
    instructors,
    name,
    notes,
    num_sections: numSections,
    num_sections_recent: numSectionsRecent,
  },
  data,
  liveData,
  selectedCourses,
}) => {
  const [contact, setContact] = useState(null)
  const [inCourseCart, setInCourseCart] = useState(
    Boolean(localStorage.getItem(code))
  )
  console.log(average)
  const {
    rInstructorQuality: avgInstructorQuality,
    rCourseQuality: avgCourseQuality,
    rDifficulty: avgDifficulty,
  } = average
  const {
    rInstructorQuality: recentInstructorQuality,
    rCourseQuality: recentCourseQuality,
    rDifficulty: recentDifficulty,
  } = recent

  const isCourse = type === 'course'
  const isInstructor = type === 'instructor'
  const isDepartment = type === 'department'

  useEffect(() => {
    if (isInstructor) apiContact(name).then(setContact)
  }, [name, isInstructor])

  const handleCartAdd = key => {
    let instructor = 'Average Professor'
    if (key !== 'average') {
      ;({
        name: instructor,
        average_reviews: average,
        recent_reviews: recent,
      } = instructors[key])
    }
    const info = Object.keys(average).map(category => ({
      category,
      average: average[category],
      recent: recent[category],
    }))
    const item = JSON.stringify({
      version: 1,
      course: code,
      instructor,
      info,
    })
    localStorage.setItem(code, item)
    if (window.onCartUpdated) window.onCartUpdated()
    setInCourseCart(true)
  }
  const handleCartRemove = () => {
    localStorage.removeItem(code)
    setInCourseCart(false)
    if (window.onCartUpdated) window.onCartUpdated()
  }

  if (!data) {
    return <h1>Loading data...</h1>
  }

  return (
    <div className="box">
      <div id="banner-info" data-type="course">
        {isCourse && (
          <CourseHeader
            aliases={aliases}
            code={code}
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

      {!isDepartment && (
        <div id="banner-score">
          <Ratings
            value="Average"
            instructor={avgInstructorQuality}
            course={avgCourseQuality}
            difficulty={avgDifficulty}
            num_sections={numSections}
          />

          <Ratings
            value="Recent"
            instructor={recentInstructorQuality}
            course={recentCourseQuality}
            difficulty={recentDifficulty}
            num_sections={numSectionsRecent}
          />
        </div>
      )}

      {isDepartment && <DepartmentGraphs courses={selectedCourses} />}

      {isCourse && <CourseDescription description={description} />}
    </div>
  )
}

export default InfoBox
