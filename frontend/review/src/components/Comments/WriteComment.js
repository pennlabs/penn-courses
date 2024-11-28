import React, { useState, forwardRef, useEffect } from "react";
import { Dropdown } from "../common/Dropdown";
import { apiPostComment, apiLive } from "../../utils/api";
import { compareSemesters } from "../../utils/helpers";
import { faTimes, faCheck, faArrowLeft, faArrowRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

export const WriteComment = forwardRef(
  (
    {
      course,
      setUserComment,
      instructor,
      semestersList,
      reply,
      setReply,
      edit,
    },
    ref
  ) => {
    const [isEditing, setIsEditing] = useState(edit ? edit : false);
    const [content, setContent] = useState("");
    const [semester, setSemester] = useState("2022A");
    const [activeSemesters, setActiveSemesters] = useState([]);

    // Log to see if the semestersList prop is updating correctly
    useEffect(() => {
      console.log("semestersList updated in WriteComment:", semestersList);
      if (semestersList) {
        const semList = semestersList.map((s) => s.semester);
        setActiveSemesters([...new Set(semList)]);
        setSemester(semList.sort(compareSemesters)[0]);
      }
    }, [semestersList]); // Update when semestersList changes

    const handleSubmit = () => {
      console.log("Comment submitted");
      console.log("Instructor");
      apiPostComment(
        course,
        semester,
        content,
        instructor,
        reply ? reply.id : null
      )
        .then((res) => {
          console.log(res);
          res = {
            ...res,
            created_at: new Date(res.created_at),
            modified_at: new Date(res.modified_at),
          };
          if (reply) {
            setReply(null);
          } else {
            setUserComment(res);
          }
        })
        .catch((err) => {
          alert("Error submitting comment");
        });
    };

    return (
      <div>
        <div
          className={`write-comment ${isEditing ? "active" : ""}`}
          onFocus={() => setIsEditing(true)}
          tabIndex={100}
          ref={ref}
        >
          {isEditing && reply === null && (
            <Dropdown name={semester}>
              {activeSemesters.map((s, i) => (
                <button
                  key={i}
                  className="btn"
                  onClick={() => {
                    setSemester(s);
                  }}
                >
                  {s}
                </button>
              ))}
            </Dropdown>
          )}
          {reply !== null && reply !== undefined && (
            <p
              style={{
                fontStyle: "italic",
                color: "#555",
                marginBottom: "10px",
              }}
            >
              Replying to <strong>{reply.author_name}</strong>
            </p>
          )}
          <textarea
            className="form-control"
            id="comment"
            rows="3"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Add a comment"
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "5px",
              border: "1px solid #ccc",
              boxShadow: "inset 0 1px 3px rgba(0, 0, 0, 0.1)",
              fontSize: "14px",
              lineHeight: "1.5",
              resize: "vertical",
            }}
          />
          {isEditing && (
            <button
              className="btn-borderless btn"
              style={{
                float: "left",
                borderRadius: "50px",
                paddingTop: "4px",
                paddingBottom: "4px",
                paddingLeft: "14px",
                paddingRight: "14px",
                transition: "color 0.3s, background-color 0.3s",
                textDecoration: "none",
              }}
              onClick={() => {
                setIsEditing(false);
                setReply(null);
              }}
              onMouseEnter={(e) => {
                e.target.style.color = "#ff6666"; // Softer red text on hover
                e.target.style.backgroundColor = "#f0f0f0"; // Grey background on hover
                e.target.style.textDecoration = "none";
              }}
              onMouseLeave={(e) => {
                e.target.style.color = "inherit";
                e.target.style.backgroundColor = "transparent";
                e.target.style.textDecoration = "none";
              }}
            >
              <FontAwesomeIcon
                icon={faTimes}
                style={{ marginRight: "5px" }}
              />
              Cancel
            </button>
          )}
          {isEditing && (
            <button
              className="btn-borderless btn"
              style={{
                float: "right",
                borderRadius: "50px",
                paddingTop: "4px",
                paddingBottom: "4px",
                paddingLeft: "14px",
                paddingRight: "14px",
                transition: "color 0.3s, background-color 0.3s",
                textDecoration: "none",
              }}
              onClick={() => handleSubmit()}
              onMouseEnter={(e) => {
                e.target.style.color = "#44dd44"; // Softer green text on hover
                e.target.style.backgroundColor = "#f0f0f0"; // Grey background on hover
                e.target.style.textDecoration = "none";
              }}
              onMouseLeave={(e) => {
                e.target.style.color = "inherit";
                e.target.style.backgroundColor = "transparent";
                e.target.style.textDecoration = "none";
              }}
            >
              <FontAwesomeIcon
                icon={faCheck}
                style={{ marginRight: "5px" }}
              />
              Comment
            </button>
          )}
        </div>
      </div>
    );
  }
);
