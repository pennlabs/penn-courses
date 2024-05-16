import React, { useState, forwardRef, useEffect } from 'react';
import { Dropdown } from '../common/Dropdown';
import { apiPostComment, apiLive } from '../../utils/api';
import { compareSemesters } from '../../utils/helpers';

export const WriteComment = forwardRef(({ course, setUserComment }, ref) => {
    const [isEditing, setIsEditing] = useState(false);
    const [content, setContent] = useState("");
    const [semester, setSemester] = useState("2022A");
    const [semestersList, setSemestersList] = useState(["2024A", "2023B", "2023A"]);

    useEffect(() => {
        if (isEditing) {
        }
    }, [course, isEditing])

    const handleSubmit = () => {
        console.log("Comment submitted");
        apiPostComment(course, semester, content).then(res => {
            setUserComment(res)
        })

    }

    return(
        <div
            className={`write-comment ${isEditing ? "active" : ""}`}
            onFocus={() => setIsEditing(true)}
            tabIndex={100}
            ref={ref}
        >
            {isEditing &&
                <Dropdown name={semester}>
                    {semestersList.map((s, i) => (
                        <button
                            key={i}
                            className="btn"
                            onClick={() => {setSemester(s); console.log(s)}}
                        >
                            {s}
                        </button>
                    ))}
                </Dropdown>}
            <textarea
                className="form-control"
                id="comment"
                rows="3"
                value={content}
                onChange={e => setContent(e.target.value)}
                placeholder="Add a comment"
            />
            {isEditing && 
                <button 
                    className="btn-borderless btn" 
                    style={{float: "left"}} 
                    onClick={() => setIsEditing(false)}
                >
                    Cancel
                </button>}
            {isEditing && 
                <button 
                    className="btn-borderless btn" 
                    style={{float: "right"}}
                    onClick={() => handleSubmit()}
                >
                    Comment
                </button>}
        </div>
    )
});