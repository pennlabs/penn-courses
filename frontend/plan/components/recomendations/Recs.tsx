import React, { useState } from "react";
import RecBanner from "./RecBanner";
import RecContent from "./RecContent";
import styled from "styled-components";
import { Course as CourseType } from "../../types";

const RecContainer = styled.div`
    margin-top: auto;
    display: flex;
    flex-direction: column;
    max-width: 48vh;
`;

interface RecsProps {
    showRecs: boolean;
    setShowRecs: React.Dispatch<React.SetStateAction<boolean>>;
    recCourses: CourseType[];
    getCourse: (id: string) => void;
    onClickDelete: () => void;
}

const Recs = ({
    showRecs,
    setShowRecs,
    recCourses,
    getCourse,
    onClickDelete,
}: RecsProps) => {
    return (
        <RecContainer>
            <RecBanner show={showRecs} setShow={setShowRecs} />
            <RecContent
                show={showRecs}
                recCourses={recCourses}
                getCourse={getCourse}
                onClickDelete={onClickDelete}
            />
        </RecContainer>
    );
};

export default Recs;
