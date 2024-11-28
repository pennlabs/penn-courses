import React, { forwardRef, useState, useEffect } from "react";
import { formatDate, truncateText } from "../../utils/helpers";
import { apiReplies } from "../../utils/api";
import { faThumbsUp, faThumbsDown, faComment } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

export const Comment = forwardRef(
  ({ comment, isUserComment, setReply }, ref) => {
    const [showReplies, setShowReplies] = useState(false);
    const [replies, setReplies] = useState([]);
    const [seeMore, setSeeMore] = useState(true);

    const [liked, setLiked] = useState(false);
    const [disliked, setDisliked] = useState(false);

    const indentation = comment.path.split(".").length; // Number of replies deep

    useEffect(() => {
      if (showReplies && replies.length === 0 && comment.replies > 0) {
        apiReplies(comment.id).then((res) => {
          setReplies(res.replies);
        });
      }
    }, [comment.id, comment.replies, replies.length, showReplies]);

    return (
      <div
        style={{
          paddingLeft: indentation === 1 ? "0" : `${2 * (indentation - 1)}vw`,
          position: "relative",
        }}
      >
        {indentation > 1 && (
          <div
            style={{
              position: "absolute",
              left: `${2 * (indentation - 1)}vw`,
              top: 0,
              bottom: 0,
              width: "2px",
              backgroundColor: "#ccc",
              borderRadius: "1px",
            }}
          ></div>
        )}
        <div
          className={`comment ${indentation !== 1 ? "reply" : ""} ${
            isUserComment ? "user" : ""
          }`}
          ref={ref}
        >
          <div className="top">
            <b>{isUserComment ? "You" : comment.author_name}</b>
            <sub>{formatDate(comment.modified_at)}</sub>
          </div>
          {seeMore ? (
            <p style={{ marginLeft: "10px" }}>{comment.text}</p>
          ) : (
            <>
              <p style={{ marginLeft: "10px" }}>
                {comment.text ? truncateText(comment.text, 150) : ""}
              </p>
              <button
                className="btn-borderless btn"
                onClick={() => setSeeMore(true)}
              >
                See More
              </button>
            </>
          )}
          <div
            className="icon-wrapper"
            style={{
              borderRadius: "50px",
              padding: "2px",
              display: "inline-block",
              transition: "background-color 0.3s",
              marginTop: "10px",
            }}
          >
            <button
              className={`btn icon ${liked ? "active" : ""}`}
              onClick={() => {
                setLiked(!liked);
                disliked && setDisliked(false);
              }}
              style={{ fontSize: "0.9em" }}
            >
              <FontAwesomeIcon icon={faThumbsUp} />
            </button>
            <span style={{ fontSize: "0.9em" }}>{comment.votes + liked - disliked}</span>
            <button
              className={`btn icon ${disliked ? "active" : ""}`}
              onClick={() => {
                setDisliked(!disliked);
                liked && setLiked(false);
              }}
              style={{ fontSize: "0.9em" }}
            >
              <FontAwesomeIcon icon={faThumbsDown} />
            </button>
          </div>
          <div
            className="icon-wrapper"
            style={{
              borderRadius: "50px",
              padding: "2px",
              display: "inline-block",
              transition: "background-color 0.3s",
              marginTop: "10px",
            }}
          >
            {!isUserComment && (
              <button
                className="btn icon"
                onClick={() => setReply(comment)}
                style={{ fontSize: "0.9em" }}
              >
                <FontAwesomeIcon icon={faComment} /> Reply
              </button>
            )}
          </div>
          {comment.replies > 0 && (
            <>
              <button
                className="btn-borderless btn"
                onClick={() => setShowReplies(!showReplies)}
              >
                {showReplies ? "Hide" : "Show"} Replies
              </button>
              <div style={{ paddingLeft: indentation !== 1 ? "0" : "2vw" }}>
                {showReplies &&
                  replies.map((reply) => (
                    <Comment key={reply.id} comment={reply} />
                  ))}
              </div>
            </>
          )}
        </div>
      </div>
    );
  }
);

// Add CSS for hover effect
const styles = `
  .icon-wrapper {
    background-color: transparent;
  }
  .icon-wrapper:hover {
    background-color: #f0f0f0;
  }
`;

// Inject styles into the document
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);
