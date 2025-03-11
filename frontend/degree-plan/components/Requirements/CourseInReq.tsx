import { useDrag } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse, DockedCourse, Fulfillment } from "@/types";
import { Draggable } from "../common/DnD";
import CourseComponent, { PlannedCourseContainer } from "../Course/Course";
import { CourseXButton } from "../Course/Course";
import { deleteFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { mutate } from "swr";

interface CourseInReqProps {
    course: DnDCourse;
    isUsed: boolean;
    isDisabled: boolean;
    rule_id: number;
    fulfillment?: Fulfillment;
    className?: string;
    activeDegreePlanId: number;
    onClick?: () => void;
}

const CourseInReq = (props : CourseInReqProps) => {
    const { course, activeDegreePlanId, rule_id } = props;

    const { remove: removeFulfillment, createOrUpdate: updateFulfillment } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`,
        { idKey: "full_code",
        // createDefaultOptimisticData: { semester: null, rules: [] }
    });
    const { createOrUpdate } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    const handleRemoveCourse = async (full_code: string) => {
        const updated_rules = course.rules?.filter(rule => rule != rule_id);
        /** If the current rule about to be removed is the only rule 
        * the course satisfied, then we delete the fulfillment */
        if (updated_rules && updated_rules.length == 0) {
          removeFulfillment(full_code);
        } else {
          updateFulfillment({rules: updated_rules}, full_code);
        }
        createOrUpdate({"full_code": full_code}, full_code); 
    }

    const [{ isDragging }, drag] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
      type: ItemTypes.COURSE_IN_REQ,
      item: {...course, rule_id: rule_id},
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging()
      })
    }), [course])
  
    return (
        <CourseComponent removeCourse={handleRemoveCourse} dragRef={drag} isDragging={isDragging} {...props} />
    )
}
  
  
  export default CourseInReq;