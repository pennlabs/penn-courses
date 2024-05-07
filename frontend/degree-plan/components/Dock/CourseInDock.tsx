import { useDrag } from "react-dnd";
import { DnDItemTypes } from "../../constants";
import { DnDCourse, DockedCourse } from "@/types";
import CourseComponent from "../Course/Course";
import { useSWRCrud } from "@/hooks/swrcrud";

interface CourseInDockProps {
    course: DnDCourse;
    isDisabled: boolean;
    className?: string;
    onClick?: () => void;
  }

const CourseInDock = (props : CourseInDockProps) => {
    const { course } = props;

    const { remove } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });
    const handleRemoveCourse = (full_code: string) => {
      remove(full_code);
    }

    const [{ isDragging }, drag] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
      type: DnDItemTypes.COURSE_IN_DOCK,
      item: course,
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging()
      })
    }), [course])
  
    return (
      <CourseComponent dragRef={drag} isDragging={isDragging} removeCourse={handleRemoveCourse} isUsed {...props} />
    )
  }
  
  
  export default CourseInDock;