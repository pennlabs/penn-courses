import React from "react";
import { RatingBox } from "./RatingBox";

export function CoursePreview({ course, style, onClick }) {
    return (
      <div
      style={{
      ...style,
      boxShadow: "0 0 14px 0 rgba(0, 0, 0, 0.07)",
      padding: "10px 10px 10px 10px",
      }}
      onClick={onClick}
      >
        <div
        style={{
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px"
        }}
        >
          <div>
            <h3
            style={{
            fontSize: "20px",
            fontWeight: "bold",
            }}
            >
              <span>{course.code}</span>: {course.title}
            </h3>
            <div
            style={{
            font: "14px",
            }}
            >
              {course.semester}
            </div>
          </div>
          <div style={{
          display: "flex",
          flexDirection: "row",
          }}>
            <RatingBox
            rating={course.quality}
            label="Quality"
            />
            <RatingBox
            rating={course.workRequired}
            label="Work"
            />
            <RatingBox
            rating={course.difficulty}
            label="Difficulty"
            />
          </div>
        </div>
        <p
        style={{
            fontSize: "14px",
            lineHeight: "16px"
        }}
        >
        {course.description}
        </p>
      </div>
    );
}