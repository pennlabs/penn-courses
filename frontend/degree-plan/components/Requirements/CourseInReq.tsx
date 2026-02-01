import { useDrag } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import { GrayIcon } from "../common/bulma_derived_components";
import styled from "@emotion/styled";
import { Course, DnDCourse, DockedCourse, Fulfillment } from "@/types";
import { Draggable } from "../common/DnD";
import CourseComponent, { PlannedCourseContainer } from "../Course/Course";
import { CourseXButton } from "../Course/Course";
import { deleteFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { mutate } from "swr";
import { useContext } from "react";
import { ExpandedCoursesPanelContext } from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";

interface CourseInReqProps {
    course: DnDCourse;
    isUsed: boolean;
    isDisabled: boolean;
    rule_id: number;
    fulfillment?: Fulfillment;
    className?: string;
    activeDegreePlanId: number;
    isOpenEnded?: boolean;
    onClick?: () => void;
}

const CourseInReq = ({
    course,
    isUsed,
    isDisabled,
    rule_id,
    fulfillment,
    activeDegreePlanId,
    isOpenEnded,
}: CourseInReqProps) => {
    const { courses, setCourses } = useContext(ExpandedCoursesPanelContext);

    const {
        remove: removeFulfillment,
        createOrUpdate: updateFulfillment,
    } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`,
        {
            idKey: "full_code",
            // createDefaultOptimisticData: { semester: null, rules: [] }
        },
    );
    const { createOrUpdate } = useSWRCrud<DockedCourse>(`/api/degree/docked`, {
        idKey: "full_code",
    });

    const handleRemoveCourse = async (full_code: string) => {
        const updated_rules = course.rules?.filter((rule) => rule != rule_id);

        // If removing course from open-ended, add to list of unselected courses.
        if (fulfillment && isOpenEnded) {
            if (courses) setCourses([...courses, fulfillment]);

            course.unselected_rules?.push(rule_id);
        }

        /** If the current rule about to be removed is the only rule
         * the course satisfied, then we delete the fulfillment */
        if (updated_rules && updated_rules.length == 0) {
            removeFulfillment(full_code);
        } else {
            if (isOpenEnded) {
                updateFulfillment(
                    {
                        rules: updated_rules,
                        unselected_rules: course.unselected_rules,
                    },
                    full_code,
                );
            } else {
                updateFulfillment({ rules: updated_rules }, full_code);
            }
        }
        createOrUpdate({ full_code: full_code }, full_code);
    };

    const [{ isDragging }, drag] = useDrag<
        DnDCourse,
        never,
        { isDragging: boolean }
    >(
        () => ({
            type: ItemTypes.COURSE_IN_REQ,
            item: { ...course, rule_id: rule_id, fulfillment: fulfillment },
            collect: (monitor) => ({
                isDragging: !!monitor.isDragging(),
            }),
        }),
        [course],
    );

    return (
        <CourseComponent
            courseType={ItemTypes.COURSE_IN_REQ}
            removeCourse={handleRemoveCourse}
            dragRef={drag}
            isDragging={isDragging}
            isDisabled={isDisabled}
            isUsed={isUsed}
            course={course}
            fulfillment={fulfillment}
        />
    );
};

export default CourseInReq;
