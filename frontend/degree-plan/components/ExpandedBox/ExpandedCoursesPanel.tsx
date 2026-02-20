import { DnDCourse, Fulfillment } from "@/types";
import styled from "@emotion/styled";
import React, { MutableRefObject, useContext, useEffect, useRef } from "react";
import CourseInExpanded from "../FourYearPlan/CourseInExpanded";
import { useSWRCrud } from "@/hooks/swrcrud";
import { DropTargetMonitor, useDrop } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import {
  ExpandedCoursesPanelContext,
  ExpandedCoursesPanelContextType,
} from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";

const useOutsideAlerter = (
  ref: MutableRefObject<any>,
  retract: () => void,
  setOpen: (arg0: boolean) => void
) => {
  const { setCourses, setRuleId, searchRef } = useContext(
    ExpandedCoursesPanelContext
  );
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        ref.current &&
        !ref.current.contains(event.target) &&
        !searchRef?.current.contains(event.target)
      ) {
        setCourses(null);
        setRuleId(null);
        retract();
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [ref]);
};

interface ExpandedCoursesPanelProps extends ExpandedCoursesPanelContextType {
  currentSemester?: string;
}

const ExpandedCoursesPanelWrapper = styled.div<{
  $left?: number;
  $right?: number;
  $top?: number;
  $bottom?: number;
  $isDroppable: boolean;
  $isOver: boolean;
}>`
    position: absolute;
    z-index: 100;
    max-height: 25vh;
    width: 25rem;
    overflow-x: hidden;
    border-radius: 10px;
    ${(props) => (props.$left ? `left: ${props.$left}px;` : "")}
    ${(props) => (props.$right ? `right: ${props.$right}px;` : "")}
    ${(props) => (props.$top ? `top: ${props.$top}px;` : "")}
    ${(props) => (props.$bottom ? `bottom: ${props.$bottom}px;` : "")}
    box-shadow: ${(props) =>
      props.$isOver
        ? "0px 0px 4px 2px var(--selected-color);"
        : props.$isDroppable
        ? "0px 0px 4px 2px var(--primary-color-dark);"
        : "rgba(0, 0, 0, 0.05);"};
    // box-shadow: 0 0 0 max(100vh, 100vw) rgba(0, 0, 0, .2);
`;

const ExpandedCoursesPanelContainer = styled.div`
  background-color: var(--primary-color-light);
  overflow: auto;
  height: 100%;
`;

const ExpandedCourses = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem 0.75rem;
  height: 100%;
  gap: 0.5rem;
  padding: 1rem;
`;

const EmptyExpandedText = styled.div`
  display: flex;
  height: 5rem;
  padding: 0 2rem;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--primary-color-extra-dark);
`;

const ExpandedCoursesHeader = styled.div`
  font-weight: bold;
`;

const CourseList = styled.div`
  // flex-grow: 1;
  gap: 0.5rem;
  display: grid;
  grid-template-columns: auto auto;
`;

const ExpandedCoursesPanel = ({
  courses,
  setCourses,
  position,
  setPosition,
  currentSemester,
  retract,
  setOpen,
  ruleId,
  searchRef,
  setSearchRef,
  degreePlanId,
}: ExpandedCoursesPanelProps) => {
  let { left, right, top, bottom } = position;

  // Set default offsets just in case left and right or top and bottom values aren't set.
  if (!left && !right) left = 0;
  if (!top && !bottom) top = 0;
  right = left === undefined ? right : undefined;
  bottom = top === undefined ? bottom : undefined;
  const wrapperRef = useRef(null);
  useOutsideAlerter(wrapperRef, retract, setOpen);

  // hooks for LEAFs
  const { createOrUpdate } = useSWRCrud<Fulfillment>(
    `/api/degree/degreeplans/${degreePlanId}/fulfillments`,
    {
      idKey: "full_code",
      createDefaultOptimisticData: { semester: null, rules: [] },
    }
  );

  const handleDrop = (course: DnDCourse) => {
    if (ruleId) {
      course.rules?.splice(course.rules?.indexOf(ruleId), 1);
      createOrUpdate(
        {
          rules: course.rules !== undefined ? course.rules : [],
          unselected_rules:
            course.unselected_rules !== undefined
              ? [...course.unselected_rules, ruleId]
              : [ruleId],
        },
        course.full_code
      );
    }

    if (courses && course.fulfillment) {
      setCourses([...courses, course.fulfillment]);
    }

    return undefined;
  }; // TODO: this doesn't handle fulfillments that already have a rule

  const handleCanDrop = (course: DnDCourse) => {
    return ruleId === course.rule_id;
  };

  const handleCollect = (monitor: DropTargetMonitor<DnDCourse, never>) => {
    return {
      isOver: !!monitor.isOver(),
      canDrop: !!monitor.canDrop(),
    };
  };

  const [{ isOver, canDrop }, drop] = useDrop<
    DnDCourse,
    never,
    { isOver: boolean; canDrop: boolean }
  >(
    {
      accept: [ItemTypes.COURSE_IN_REQ],
      drop: handleDrop,
      canDrop: handleCanDrop,
      collect: handleCollect,
    },
    [createOrUpdate]
  );

  return (
    <ExpandedCoursesPanelWrapper
      $right={right}
      $left={left}
      $top={top}
      $bottom={bottom}
      $isDroppable={canDrop}
      $isOver={isOver}
      ref={drop}
    >
      <ExpandedCoursesPanelContainer ref={wrapperRef}>
        <ExpandedCourses>
          <ExpandedCoursesHeader>Also satisfied by...</ExpandedCoursesHeader>
          {courses && courses?.length > 0 ? (
            <CourseList>
              {courses?.map((fulfillment) => (
                <CourseInExpanded
                  course={fulfillment}
                  rule_id={ruleId ? ruleId : 0}
                  fulfillment={fulfillment}
                  isDisabled={false}
                  activeDegreePlanId={fulfillment.degree_plan}
                />
              ))}
            </CourseList>
          ) : (
            <EmptyExpandedText>
              Drag any extra courses here that you don't want to use for this
              requirement.
            </EmptyExpandedText>
          )}
        </ExpandedCourses>
      </ExpandedCoursesPanelContainer>
    </ExpandedCoursesPanelWrapper>
  );
};

export default ExpandedCoursesPanel;
