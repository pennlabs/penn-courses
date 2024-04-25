import React, { forwardRef, useState, useEffect } from "react";
import { formatDate, truncateText } from "../../utils/helpers";
import { apiReplies } from "../../utils/api";

export const Comment = forwardRef(({ comment, isReply }, ref) => {
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState([]);
  const [seeMore, setSeeMore] = useState(comment.content.length < 150);

  useEffect(() => {
    if (showReplies && replies.length === 0 && comment.replies > 0) {
      apiReplies(comment.id).then(res => {
        console.log(res);
        setReplies(res.replies);
      });
    }
  }, [comment.id, comment.replies, replies.length, showReplies]);

  return (
    <div className={`comment ${isReply ? "reply" : ""}`} ref={ref}>
      <div className="left">
        <div className="top">
          <b>{comment.author_name}</b>
          <sub>{formatDate(comment.modified_at)}</sub>
        </div>
        {seeMore ? (
          <p>{comment.content}</p>
        ) : (
          <>
            <p>{truncateText(comment.content, 150)}</p>
            <button
              className=" btn-borderless btn"
              onClick={() => setSeeMore(true)}
            >
              See More
            </button>
          </>
        )}
        {comment.replies > 0 && (
          <>
            <button
              className="btn-borderless btn"
              onClick={() => setShowReplies(!showReplies)}
            >
              {showReplies ? "Hide" : "Show"} Replies
            </button>
            {showReplies &&
              replies.map(reply => (
                <Comment key={reply.id} comment={reply} isReply />
              ))}
          </>
        )}
      </div>
      <div className="right">
        <i className="fas fa-thumbs-up"></i>
        <span>{comment.likes}</span>
      </div>
    </div>
  );
});
