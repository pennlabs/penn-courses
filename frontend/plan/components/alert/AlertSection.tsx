import React from "react";
import styled from "styled-components";
import { isMobile } from "react-device-detect";
import { Alert } from "../../types";
import AlertButton from "./AlertButton";
import { Section as SectionType, Alert as AlertType } from "../../types";

interface AlertDetailsProps {
    alert: Alert;
}

const CourseDetailsContainer = styled.div`
    flex-grow: 0;
    display: flex;
    flex-direction: column;
    text-align: left;
    align-items: left;
`;

const StatusInd = styled.div<{ background: string }>`
    display: inline-block;
    border-radius: 1rem;
    width: 0.4rem;
    height: 0.4rem;
    margin-right: 0.2rem;
    background-color: ${(props) => props.background};
`;

const CourseDetails = ({ alert }: AlertDetailsProps) => {
    let statustext;
    let statuscolor;

    if(alert.status === "O") {
        statustext = "Open";
        statuscolor = "#78d381";
    } else {
        statustext = "Closed";
        statuscolor = "#e1e6ea";
    }

    return(
        <CourseDetailsContainer>
            <b>
                <span>{alert.section.replace(/-/g, " ")}</span>
            </b>
            <div style={{ fontSize: "0.8rem", position: "relative" }}>
                <StatusInd background={statuscolor} />
                {statustext}
            </div>
        </CourseDetailsContainer>
    );
};

const AlertCourseButton = styled.div.attrs({ className: "btn" })`
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
    <AlertCourseButton role="button" onClick={courseInfo}>
        <i className="fa fa-info-circle" />
    </AlertCourseButton>
);

interface CourseTrashCanProps {
    remove: (event: React.MouseEvent<HTMLDivElement>) => void;
}

const CourseTrashCan = ({ remove }: CourseTrashCanProps) => (
    <AlertCourseButton role="button" onClick={remove}>
        <i className="fas fa-trash" />
    </AlertCourseButton>
);

interface AlertSectionProps {
    alert: Alert;
    inAlerts: boolean;
    alerts?: {
        add: () => void;
        remove: () => void;
        delete: () => void;
    };
    courseInfo: (event: React.MouseEvent<HTMLDivElement>) => void;
}

const AlertItem = styled.div<{ isMobile: boolean }>`
    background: white;
    transition: 250ms ease background;
    user-select: none;

    display: grid;
    padding: 0.8rem;
    border-bottom: 1px solid #e5e8eb;
    grid-template-columns: 20% 50% 15% 15%;
    * {
        user-select: none;
    }
    &:hover {
        background: #f5f5ff;
    }

    &:hover .btn i {
        cursor: pointer;
        color: #d3d3d8;
    }
`;

const AlertSection: React.FC<AlertSectionProps> = ({
    alert,
    alerts,
    inAlerts,
    courseInfo,
}) => {
    return(
        <AlertItem
            role="switch"
            id={alert.id}
            aria-checked="false"
            isMobile={isMobile}
        >
                <AlertButton
                    alerts={alerts}
                    inAlerts={inAlerts}
                />
            <CourseDetails alert={alert} />
            <CourseInfoButton courseInfo={courseInfo} />
            <CourseTrashCan remove={(event) => {
                event.stopPropagation();
                alerts?.delete();
            }} />
        </AlertItem>
    )
};

export default AlertSection;
