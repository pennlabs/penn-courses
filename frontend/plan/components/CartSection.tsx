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
    max-width: 70%;
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
                        style={{ paddingRight: "5px" }}
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

interface CourseInfoButtonProps {
    courseInfo: () => void;
}

const CourseInfoButton = ({ courseInfo }: CourseInfoButtonProps) => (
    <div role="button" onClick={courseInfo} className="cart-delete-course">
        <i className="fa fa-info-circle" />
    </div>
);

interface CourseTrashCanProps {
    remove: () => void;
}

const CourseTrashCan = ({ remove }: CourseTrashCanProps) => (
    <div role="button" onClick={remove} className="cart-delete-course">
        <i className="fas fa-trash" />
    </div>
);

interface CartSectionProps {
    meetings: Meeting[];
    code: string;
    checked: boolean;
    overlaps: boolean;
    toggleCheck: () => void;
    remove: () => void;
    courseInfo: () => void;
    lastAdded: boolean;
}

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
    <div
        role="switch"
        id={code}
        aria-checked="false"
        className={
            lastAdded ? "course-cart-item highlighted" : "course-cart-item"
        }
        style={
            !isMobile
                ? {
                      display: "flex",
                      flexDirection: "row",
                      justifyContent: "space-around",
                      padding: "0.8rem",
                      borderBottom: "1px solid #E5E8EB",
                  }
                : {
                      display: "grid",
                      gridTemplateColumns: "20% 50% 15% 15%",
                      padding: "0.8rem",
                      borderBottom: "1px solid #E5E8EB",
                  }
        }
        onClick={(e) => {
            // ensure that it's not the trash can being clicked
            if (
                // NOTE: explicit typecase and not null assertion operator used
                (e.target as HTMLElement).parentElement!.getAttribute(
                    "class"
                ) !== "cart-delete-course"
            ) {
                toggleCheck();
            }
        }}
    >
        <CourseCheckbox checked={checked} />
        <CourseDetails meetings={meetings} code={code} overlaps={overlaps} />
        <CourseInfoButton courseInfo={courseInfo} />
        <CourseTrashCan remove={remove} />
    </div>
);

export default CartSection;
