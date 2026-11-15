import { useDrag } from "react-dnd";
import { useCourseDragPreview } from "@/components/common/CourseDragPreview";
import { ItemTypes } from "../Dock/dnd/constants";
import { Course, DnDCourse, Fulfillment } from "@/types";
import 'react-loading-skeleton/dist/skeleton.css'
import CourseComponent from "../Course/Course";

interface CoursePlannedProps {
  course: Fulfillment;
  removeCourse: (course: Course["id"]) => void;
  semester: Course["semester"];
  isDisabled: boolean;
  className?: string;
  onClick?: (arg0: React.MouseEvent<HTMLInputElement>) => void;
}

const CourseInPlan = (props : CoursePlannedProps) => {
  const { course } = props;
  
  const [{ isDragging }, drag, preview] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
    type: ItemTypes.COURSE_IN_PLAN,
    item: course,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }), [course])
  useCourseDragPreview(preview);

  return (
    <CourseComponent courseType={ItemTypes.COURSE_IN_PLAN} fulfillment={course as Fulfillment} dragRef={drag} isDragging={isDragging} isUsed {...props} />
  )
}

export default CourseInPlan;