import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse, DockedCourse, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";
import { CourseXButton, PlannedCourseContainer } from "../FourYearPlan/CourseInPlan";
import { useSWRCrud } from "@/hooks/swrcrud";

interface CourseInDockProps {
    course: DnDCourse;
    isUsed: boolean;
    isDisabled: boolean;
    className?: string;
    onClick?: () => void;
  }

const CourseInDock = ({ course, isUsed = false, isDisabled = false, className, onClick } : CourseInDockProps) => {
    const { remove } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    const handleRemoveCourse = (full_code: string) => {
      remove(full_code);
    }

    const [{ isDragging }, drag] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
      type: ItemTypes.COURSE_IN_DOCK,
      item: course,
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
                {isUsed && <CourseXButton onClick={() => handleRemoveCourse(course.full_code)} />}
            </PlannedCourseContainer>
          </ReviewPanelTrigger>
        </Draggable>
      </div>
    )
  }
  
  
  export default CourseInDock;