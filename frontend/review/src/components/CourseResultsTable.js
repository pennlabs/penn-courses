import React, { useState, useCallback, useMemo, useRef } from "react";
import { useHistory } from "react-router-dom/cjs/react-router-dom.min";
import { ScoreTable } from "./common/ScoreTable"; 
import { ColumnSelector } from "./common/ColumnSelector";
import { COLUMN_FULLNAMES, ALL_DATA_COLUMNS } from "../constants";

const REQUIRED_REVIEW_FIELDS = [
  // "rCourseQuality",
  // "rInstructorQuality",
  // "rDifficulty",
  "course_quality",
  "instructor_quality",
  "difficulty",
  "work_required",
];

const buildData = (courses, allReviewFields) =>
  Object.entries(courses).map(([key, course]) => {
    const avg = course.average_reviews || {};
    const rec = course.recent_reviews || {};

    const row = {
      key,
      code: course.code || course.id,
      name: course.name,
    };

    allReviewFields.forEach((field) => {
      row[field] = {
        average: avg[field] != null ? avg[field].toFixed(2) : null,
        recent: rec[field] != null ? rec[field].toFixed(2) : null,
      };
    });

    return row;
  });

const buildColumns = (allReviewFields, isAverageRef) => {
  const fixed = [
    {
      Header: "Course",
      accessor: "name",
      id: "name",
      required: true,
      show: true,
      minWidth: 200,
    },
    {
      Header: "Code",
      accessor: "code",
      id: "code",
      required: true,
      show: true,
      minWidth: 100,
      Cell: ({ value }) => {
        const history = useHistory();
        return (
          <div className="course-code-cell">
            <span onClick={() => history.push(`/course/${value}`)}>{value}</span>
          </div>
        );
      },
    },
  ];

  const reviewColumns = allReviewFields.map((field) => {
    const label = COLUMN_FULLNAMES[field] || field;
    const isRequired = REQUIRED_REVIEW_FIELDS.includes(field);

    return {
      Header: label,
      id: field,
      accessor: field,
      required: isRequired,
      show: isRequired,
      width: 150,
      sortMethod: (a, b) => {
        const aVal = a
          ? isAverageRef.current
            ? a.average
            : a.recent
          : null;
        const bVal = b
          ? isAverageRef.current
            ? b.average
            : b.recent
          : null;
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;
        return parseFloat(aVal) - parseFloat(bVal);
      },
      Cell: ({ value = {} }) => {
        const { average, recent } = value;
        const display = isAverageRef.current ? average : recent;
        const val = display != null ? display : "N/A";
        const className = isAverageRef.current
          ? "cell_average"
          : "cell_recent";
        return (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", maxHeight: "100%" }}>
            <span className={val === "N/A" ? "empty" : className}>{val}</span>
          </div>
        );
      },
    };
  });

  return [...fixed, ...reviewColumns];
};

const CourseResultsTable = ({ filteredResults, isAverage }) => {

  // Ref lets Cell renderers and sortMethods always read the current value
  // without needing to rebuild columns when the toggle changes.
  const isAverageRef = useRef(isAverage);
  isAverageRef.current = isAverage;

  const [columns, setColumns] = useState(() =>
    buildColumns(ALL_DATA_COLUMNS, isAverageRef)
  );

  const data = useMemo(
    () => buildData(filteredResults, ALL_DATA_COLUMNS),
    [filteredResults]
  );

  const handleColumnSelect = useCallback((updatedColumns) => {
    setColumns(updatedColumns);
  }, []);

  if (data.length === 0) {
    return <p>No results</p>;
  }

  const visibleColumns = columns.filter((col) => col.show);

  return (
    <div className="course-results-table-container" style={{display: "flex", flexDirection: "column", gap: "12px", height: 'fit-content'}}>
      <div className="clearfix">
        <ColumnSelector
          className="course-results-column-selector"
          buttonStyle="course-results-btn"
          name="courseResults"
          columns={columns}
          onSelect={handleColumnSelect}
        />
      </div>
      <ScoreTable
        style={{ maxHeight: "100vh" }}
        className="course-results-table"
        columns={visibleColumns}
        data={data}
        noun="course"
        sorted={[{ id: "code", desc: false }]}
        isAverage={isAverage}
      />
    </div>
  );
};

export default CourseResultsTable;