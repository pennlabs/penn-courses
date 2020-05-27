import React from 'react'

/**
 * Three colored boxes with numerical rating values, used in the course description box.
 */
const RatingRow = ({
  value,
  num_sections: numSections,
  course,
  instructor,
  difficulty,
}) => {
  const numOrNA = num => (isNaN(num) ? 'N/A' : num.toFixed(1))
  // TODO: After switching to styled-components or some other styling solution, refactor this code.
  const getColor = num => {
    if (isNaN(num)) {
      return 'rating-good'
    }
    num = num.toFixed(1)
    if (num < 2) {
      return 'rating-bad'
    }
    if (num < 3) {
      return 'rating-okay'
    }
    return 'rating-good'
  }

  const hasSingleSection = numSections === 1

  return (
    <div className="scorebox-desc-row">
      <div className="scoredesc">
        <p className="title">{value}</p>{' '}
        <p className="subtitle">
          {numSections} {hasSingleSection ? 'Section' : 'Sections'}
        </p>
      </div>
      <div className="scoreboxrow">
        <div className={`scorebox course ${getColor(course)}`}>
          <p className="num">{numOrNA(course)}</p>
          <p className="desc">Course</p>
        </div>
        <div className={`scorebox instructor ${getColor(instructor)}`}>
          <p className="num">{numOrNA(instructor)}</p>
          <p className="desc">Instructor</p>
        </div>
        <div className={`scorebox difficulty ${getColor(difficulty)}`}>
          <p className="num">{numOrNA(difficulty)}</p>
          <p className="desc">Difficulty</p>
        </div>
      </div>
    </div>
  )
}

export default RatingRow
