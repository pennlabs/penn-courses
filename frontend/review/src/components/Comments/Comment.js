import React, { forwardRef, useState, useEffect } from "react";
import { formatDate, truncateText } from "../../utils/helpers";
import { apiReplies } from "../../utils/api";
import { faThumbsUp, faThumbsDown } from "@fortawesome/free-solid-svg-icons"
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'

export const Comment = forwardRef(({ comment, isReply, isUserComment }, ref) => {
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState([]);
  const [seeMore, setSeeMore] = useState(comment.text.length < 150);

  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);

  useEffect(() => {
    if (showReplies && replies.length === 0 && comment.replies > 0) {
      apiReplies(comment.id).then(res => {
        setReplies(res.replies);
      });
    }
  }, [comment.id, comment.replies, replies.length, showReplies]);

  return (
    <div className={`comment ${isReply ? "reply" : ""} ${isUserComment ? "user" : ""}`} ref={ref}>
        <div className="top">
          <b>{isUserComment ? "You" : comment.author_name}</b>
          <sub>{formatDate(comment.modified_at)}</sub>
        </div>
        {seeMore ? (
          <p>{comment.text}</p>
        ) : (
          <>
            <p>{truncateText(comment.text, 150)}</p>
            <button
              className=" btn-borderless btn"
              onClick={() => setSeeMore(true)}
            >
              See More
            </button>
          </>
        )}
        <div className="icon-wrapper">
          <button className={`btn icon ${liked ? "active" : ""}`} onClick={() => {setLiked(!liked); disliked && setDisliked(false)}}><FontAwesomeIcon icon={faThumbsUp} /></button>
          <span>{comment.votes + liked - disliked}</span>
          <button className={`btn icon ${disliked ? "active" : ""}`} onClick={() => {setDisliked(!disliked); liked && setLiked(false)}}><FontAwesomeIcon icon={faThumbsDown} /></button>
        </div>
        {comment.replies > 0 && (
          <>
            <button
              className="btn-borderless btn"
              onClick={() => setShowReplies(!showReplies)}
            >
              {showReplies ? "Hide" : "Show"} Replies
            </button>
            <div style={{ paddingLeft: isReply ? "0" : "2vw" }}>
              {showReplies &&
                replies.map(reply => (
                  <Comment key={reply.id} comment={reply} isReply />
                ))}
            </div>
         </>
        )}
    </div>
  );
});
