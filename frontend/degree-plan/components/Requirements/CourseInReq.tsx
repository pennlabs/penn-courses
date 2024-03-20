import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";
import { PlannedCourseContainer } from "../FourYearPlan/CourseInPlan";

interface CourseInReqProps {
    course: DnDCourse;
    removeCourse: (course: Course["full_code"]) => void;
    semester: Course["semester"];
    isUsed: boolean;
    isDisabled: boolean;
    rule_id: number;
    className?: string;
    onClick?: () => void;
  }

const CourseInReq = ({ course, removeCourse, isUsed = false, isDisabled = false, className, onClick, rule_id } : CourseInReqProps) => {
    const [{ isDragging }, drag] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
      type: ItemTypes.COURSE_IN_REQ,
      item: {...course, rule_id: rule_id},
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging()
      })
    }), [course])
  
    return (
      <div onClick={onClick}>
        <Draggable
        isDragging={isDragging}
        >
          <ReviewPanelTrigger full_code={course.full_code}>
            <PlannedCourseContainer
            $isDragging={isDragging}
            $isUsed={isUsed}
            $isDisabled={isDisabled}
            ref={drag}
            className={className}
            >
                <div>
                  {course.full_code}
                </div>
                {isUsed &&
                  <GrayIcon className="close-button" onClick={() => removeCourse(course.full_code)}>
                    <i className="fas fa-times"></i>
                  </GrayIcon>
                  }
            </PlannedCourseContainer>
          </ReviewPanelTrigger>
        </Draggable>
      </div>
    )
  }
  
  
  export default CourseInReq;