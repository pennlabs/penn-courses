import { ConnectDragSource } from "react-dnd";
import { GrayIcon, Icon } from "@/components/common/bulma_derived_components";
import styled from "@emotion/styled";
import { Course, DnDCourse, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "@/components/Infobox/ReviewPanel";
import { Draggable } from "@/components/common/DnD";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { Tooltip } from "react-tooltip";

const DOUBLE_COUNT_ERROR_MESSAGE =
    "This course is being illegally double counted in your plan!";
const COURSE_BORDER_RADIUS = "9px";

export const BaseCourseContainer = styled.div<{
    $isDragging?: boolean;
    $isUsed: boolean;
    $isDisabled: boolean;
}>`
    display: flex;
    justify-content: center;
    align-items: center;
    min-width: 70px;
    min-height: 35px;
    border-radius: ${COURSE_BORDER_RADIUS};
    padding: 0.75rem;
    text-wrap: nowrap;
    cursor: ${(props) =>
        props.$isDisabled || props.$isUsed ? "not-allowed" : "grab"};
    opacity: ${(props) => (props.$isDisabled || props.$isDragging ? 0.7 : 1)};
    background-color: ${(props) =>
        props.$isDragging ? "#4B9AE7" : "var(--background-grey)"};
    box-shadow: rgba(0, 0, 0, 0.01) 0px 6px 5px 0px,
        rgba(0, 0, 0, 0.04) 0px 0px 0px 1px;
`;

export const PlannedCourseContainer = styled(BaseCourseContainer)`
    width: 100%;
    position: relative;
    opacity: ${(props) => (props.$isDragging ? 0.5 : 1)};

    .close-button {
        padding-left: 1rem;
        padding-right: 10px;
        margin-top: auto;
        margin-bottom: auto;
        height: 100%;
        align-items: center;
        opacity: 0.6;
    }

    .illegal-icon {
        padding-right: 0.5rem;
        margin-top: auto;
        margin-bottom: auto;
    }

    &:hover {
        .close-button {
            opacity: unset;
        }
    }
`;

const CloseIcon = styled(GrayIcon)<{ $hidden: boolean }>`
    visibility: ${(props) => (props.$hidden ? "hidden" : "visible")};
`;

export const CourseXButton = ({
    onClick,
    hidden,
}: {
    onClick?: (e: React.MouseEvent<HTMLInputElement>) => void;
    hidden: boolean;
}) => (
    <CloseIcon className="close-button" onClick={onClick} $hidden={hidden}>
        <i className="fas fa-times"></i>
    </CloseIcon>
);

interface DraggableComponentProps {
    courseType: string;
    course: DnDCourse;
    removeCourse: (course: Course["id"]) => void;
    semester?: Course["semester"];
    isUsed: boolean;
    isDisabled: boolean;
    isDragging: boolean;
    fulfillment?: Fulfillment;
    className?: string;
    onClick?: (arg0: React.MouseEvent<HTMLInputElement>) => void;
    dragRef: ConnectDragSource;
}

export const SkeletonCourse = () => (
    <PlannedCourseContainer $isUsed={false} $isDisabled={false}>
        <Skeleton width="5em" />
    </PlannedCourseContainer>
);

const CourseBadge = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.25rem;
`;

const IconBadge = styled.div`
    padding: 0.2rem;
    border-radius: 5px;
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.07rem;
    background-color: #ebebeb;

    p {
        font-size: 14px;
        font-weight: bold;
    }
`;

const ExclamationIcon = ({ color }: { color: string }) => {
    const Exclamation = styled(Icon)`
        width: 1rem;
        height: 1rem;
        display: flex;
        fill: ${color};
    `;

    return (
        <Exclamation>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                <path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zm0-384c13.3 0 24 10.7 24 24l0 112c0 13.3-10.7 24-24 24s-24-10.7-24-24l0-112c0-13.3 10.7-24 24-24zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z" />
            </svg>
        </Exclamation>
    );
};

const SemesterIcon = ({ semester }: { semester: string | null }) => {
    if (!semester) return <div></div>;
    const year =
        semester === TRANSFER_CREDIT_SEMESTER_KEY
            ? "AP"
            : semester.substring(2, 4);
    const sem = semester.substring(4);

    return (
        <IconBadge>
            <p>{year}</p>
            {sem === "A" && <i className="spring-icon"></i>}
            {sem === "B" && <i className="summer-icon"></i>}
            {sem === "C" && <i className="fall-icon"></i>}
        </IconBadge>
    );
};

const CourseComponent = ({
    courseType,
    course,
    fulfillment,
    removeCourse,
    isUsed = false,
    isDisabled = false,
    className,
    onClick,
    isDragging,
    dragRef,
}: DraggableComponentProps) => {
    if (!!fulfillment) {
        return (
            <Draggable isDragging={isDragging} onClick={onClick}>
                <ReviewPanelTrigger
                    full_code={course.full_code}
                    triggerType="click"
                >
                    <PlannedCourseContainer
                        $isDragging={isDragging}
                        $isUsed={isUsed}
                        $isDisabled={isDisabled}
                        ref={dragRef}
                        className={className}
                    >
                        {!fulfillment?.legal && (
                            <div style={{ paddingRight: "5px" }}>
                                <a
                                    data-tooltip-id={
                                        fulfillment.full_code + courseType
                                    }
                                    data-tooltip-content={
                                        DOUBLE_COUNT_ERROR_MESSAGE
                                    }
                                >
                                    <ExclamationIcon color={"#E66161"} />
                                </a>
                                <Tooltip
                                    id={fulfillment.full_code + courseType}
                                    place="top"
                                />
                            </div>
                        )}
                        <CourseBadge>
                            {course.full_code.replace("-", " ")}
                            {fulfillment.semester !== "" && (
                                <SemesterIcon semester={fulfillment.semester} />
                            )}
                        </CourseBadge>
                        {isUsed && (
                            <CourseXButton
                                onClick={(e) => {
                                    removeCourse(course.full_code);
                                    e.stopPropagation();
                                }}
                                hidden={false}
                            />
                        )}
                    </PlannedCourseContainer>
                </ReviewPanelTrigger>
            </Draggable>
        );
    }
    return (
        <Draggable isDragging={isDragging} onClick={onClick}>
            <ReviewPanelTrigger
                full_code={course.full_code}
                triggerType="click"
            >
                <PlannedCourseContainer
                    $isDragging={isDragging}
                    $isUsed={isUsed}
                    $isDisabled={isDisabled}
                    ref={dragRef}
                    className={className}
                >
                    <CourseBadge>
                        {course.full_code.replace("-", " ")}
                    </CourseBadge>
                    {isUsed && (
                        <CourseXButton
                            onClick={(e) => {
                                removeCourse(course.full_code);
                                e.stopPropagation();
                            }}
                            hidden={false}
                        />
                    )}
                </PlannedCourseContainer>
            </ReviewPanelTrigger>
        </Draggable>
    );
};

export default CourseComponent;
