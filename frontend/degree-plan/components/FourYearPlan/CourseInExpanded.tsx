import { useDrag } from "react-dnd";
import { ItemTypes } from "@/components/Dock/dnd/constants";
import { DnDCourse, DockedCourse, Fulfillment } from "@/types";
import CourseComponent from "@/components/Course/Course";
import { useSWRCrud } from "@/hooks/swrcrud";
import styled from "styled-components";

interface CourseInReqProps {
  course: DnDCourse;
  isDisabled: boolean;
  rule_id: number;
  fulfillment?: Fulfillment;
  className?: string;
  activeDegreePlanId: number;
  
  onClick?: () => void;
}

const CourseComponentContainer = styled.div`
  display: inline-block;
  width: 100%;
`

const CourseInExpanded = ( { course, isDisabled, rule_id, fulfillment, activeDegreePlanId } : CourseInReqProps) => {
    const { remove: removeFulfillment, createOrUpdate: updateFulfillment } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`, { idKey: "full_code" });
    const { createOrUpdate } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    const handleRemoveCourse = async (full_code: string) => {
        const updatedRules = course.rules?.filter(rule => rule != rule_id);
        /** If the current rule about to be removed is the only rule 
        * the course satisfied, then we delete the fulfillment */
        if (updatedRules && updatedRules.length == 0) {
          removeFulfillment(full_code);
        } else {
          updateFulfillment({rules: updatedRules}, full_code);
        }
        createOrUpdate({"full_code": full_code}, full_code); 
    }

    const [{ isDragging }, drag] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
      type: ItemTypes.COURSE_IN_EXPAND,
      item: {...course, rule_id: rule_id},
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging()
      })
    }), [course])
  
    return (
      <CourseComponentContainer>
        <CourseComponent 
          courseType={ItemTypes.COURSE_IN_EXPAND} 
          removeCourse={handleRemoveCourse} 
          dragRef={drag} 
          isUsed={false} 
          isDragging={isDragging} 
          isDisabled={isDisabled}
          course={course}
          fulfillment={fulfillment}
        />
      </CourseComponentContainer>
    )
}
 
export default CourseInExpanded;