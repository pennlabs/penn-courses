import React, { useState } from "react";
import styled from "styled-components";
import RecBanner from "./RecBanner";
import RecContent from "./RecContent";
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
    fetchStatus: number;
    setRefresh: React.Dispatch<React.SetStateAction<boolean>>;
}

const Recs = ({
    showRecs,
    setShowRecs,
    recCourses,
    getCourse,
    fetchStatus,
    setRefresh,
}: RecsProps) => {
    return (
        <RecContainer>
            <RecBanner
                show={showRecs}
                setShow={setShowRecs}
                setRefresh={setRefresh}
            />
            <RecContent
                show={showRecs}
                recCourses={recCourses}
                getCourse={getCourse}
                fetchStatus={fetchStatus}
            />
        </RecContainer>
    );
};

export default Recs;
