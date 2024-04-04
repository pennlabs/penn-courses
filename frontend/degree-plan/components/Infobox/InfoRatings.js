import React from "react";

/**
 * Three colored boxes with numerical rating values, used in the course description box.
 */
const RatingRow = ({ value, course, instructor, difficulty, work }) => {
  const numOrNA = (num) => (!num || isNaN(num) ? "N/A" : num.toFixed(1));
  const getColor = (_num, reverse) => {
    if (!_num || isNaN(_num)) {
      return "rating-good";
    }
    const num = _num.toFixed(1);
    if (num < 2) {
      return reverse ? "rating-good" : "rating-bad";
    }
    if (num < 3) {
      return "rating-okay";
    }
    return reverse ? "rating-bad" : "rating-good";
  };

  return (
    <div className="scorebox-desc-row">
      <div className="scoredesc">
        <p className="title">{value}</p>{" "}
      </div>
      <div className="scoreboxrow">
        <div className={`scorebox course ${getColor(course, false)}`}>
          <p className="num">{numOrNA(course)}</p>
          <p className="desc">Course</p>
        </div>
        <div className={`scorebox instructor ${getColor(instructor, false)}`}>
          <p className="num">{numOrNA(instructor)}</p>
          <p className="desc">Instructor</p>
        </div>
        <div className={`scorebox difficulty ${getColor(difficulty, true)}`}>
          <p className="num">{numOrNA(difficulty)}</p>
          <p className="desc">Difficulty</p>
        </div>
        <div className={`scorebox work ${getColor(work, true)}`}>
          <p className="num">{numOrNA(work)}</p>
          <p className="desc">Work</p>
        </div>
      </div>
    </div>
  );
};

export default RatingRow;
