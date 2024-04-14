import React from "react";
import styled from "styled-components";
import { isMobile } from "react-device-detect";
import { getTimeString } from "./meetUtil";

import { Meeting } from "../types";

interface CourseDetailsProps {
    meetings: Meeting[];
    code: string;
    overlaps: boolean;
}

const CourseDetailsContainer = styled.div`
    flex-grow: 0;
    display: flex;
    flex-direction: column;
    text-align: left;
    align-items: left;
`;

const CourseDetails = ({ meetings, code, overlaps }: CourseDetailsProps) => (
    <CourseDetailsContainer>
        <b>
            <span>{code.replace(/-/g, " ")}</span>
        </b>
        <div style={{ fontSize: "0.8rem" }}>
            {overlaps && (
                <div className="popover is-popover-right">
                    <i
                        style={{ paddingRight: "5px", color: "#c6c6c6" }}
                        className="fas fa-calendar-times"
                    />
                    <span className="popover-content">
                        Conflicts with schedule!
                    </span>
                </div>
            )}
            {getTimeString(meetings)}
        </div>
    </CourseDetailsContainer>
);

interface CourseCheckboxProps {
    checked: boolean;
}

const CourseCheckbox = ({ checked }: CourseCheckboxProps) => {
    const checkStyle = {
        width: "1rem",
        height: "1rem",
        border: "none",
        color: "#878ED8",
    };
    return (
        <div
            aria-checked="false"
            role="checkbox"
            style={{
                flexGrow: 0,
                flexDirection: "row",
                alignItems: "center",
                justifyContent: "center",
                display: "flex",
                fontSize: "18px",
            }}
        >
            <i
                className={`${
                    checked ? "fas fa-check-square" : "far fa-square"
                }`}
                style={checkStyle}
            />
        </div>
    );
};

const CartCourseButton = styled.div`
    flex-grow: 0;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    display: flex;

    i {
        width: 1rem;
        height: 1rem;
        transition: 250ms ease all;
        border: none;
        color: #d3d3d800;
    }

    i:hover {
        color: #67676a !important;
    }
`;

interface CourseInfoButtonProps {
    courseInfo: (event: React.MouseEvent<HTMLDivElement>) => void;
}

const CourseInfoButton = ({ courseInfo }: CourseInfoButtonProps) => (
    <CartCourseButton role="button" onClick={courseInfo}>
        <i className="fa fa-info-circle" />
    </CartCourseButton>
);

interface CourseTrashCanProps {
    remove: (event: React.MouseEvent<HTMLDivElement>) => void;
}

const CourseTrashCan = ({ remove }: CourseTrashCanProps) => (
    <CartCourseButton role="button" onClick={remove}>
        <i className="fas fa-trash" />
    </CartCourseButton>
);

interface CartSectionProps {
    meetings: Meeting[];
    code: string;
    checked: boolean;
    overlaps: boolean;
    toggleCheck: () => void;
    remove: (event: React.MouseEvent<HTMLDivElement>) => void;
    courseInfo: (event: React.MouseEvent<HTMLDivElement>) => void;
    lastAdded: boolean;
}

const CourseCartItem = styled.div<{ $lastAdded: boolean; $isMobile: boolean }>`
    background: ${(props) => (props.$lastAdded ? "#e1e3f7" : "white")};
    transition: 250ms ease background;
    cursor: pointer;
    user-select: none;

    display: grid;
    flex-direction: row;
    padding: 0.8rem;
    border-bottom: 1px solid #e5e8eb;
    grid-template-columns: 20% 50% 15% 15%;
    * {
        user-select: none;
    }
    &:hover {
        background: #f5f5ff;
    }
    &:active {
        background: #efeffe;
    }

    &:hover i {
        color: #d3d3d8;
    }
`;

const CartSection = ({
    toggleCheck,
    checked,
    code,
    meetings,
    remove,
    courseInfo,
    overlaps,
    lastAdded,
}: CartSectionProps) => (
    <CourseCartItem
        role="switch"
        id={code}
        aria-checked="false"
        $lastAdded={lastAdded}
        $isMobile={isMobile}
        onClick={toggleCheck}
    >
        <CourseCheckbox checked={checked} />
        <CourseDetails meetings={meetings} code={code} overlaps={overlaps} />
        <CourseInfoButton courseInfo={courseInfo} />
        <CourseTrashCan remove={remove} />
    </CourseCartItem>
);

export default CartSection;
