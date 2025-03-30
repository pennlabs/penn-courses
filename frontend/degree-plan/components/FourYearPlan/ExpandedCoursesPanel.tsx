import { DnDCourse, Fulfillment } from '@/types';
import Draggable from 'react-draggable';
import useSWR from 'swr';
import styled from '@emotion/styled';
import InfoBox from './index'
import React, { MutableRefObject, PropsWithChildren, useContext, useEffect, useRef, useState } from 'react';
import { createContext } from 'react';
import { RightCurriedFunction1 } from 'lodash';
import CourseInExpanded from './CourseInExpanded';
import { useSWRCrud } from '@/hooks/swrcrud';
import { useDrop } from 'react-dnd';
import { ItemTypes } from '../Dock/dnd/constants';

const REVIEWPANEL_TRIGGER_TIME = 200 // in ms, how long you have to hover for review panel to open

const useOutsideAlerter = (ref: any, retract: () => void, set_open: (arg0: boolean) => void) => {
    const { set_courses, set_rule_id, search_ref } = useContext(ExpandedCoursesPanelContext);
    useEffect(() => {
        /**
         * Alert if clicked on outside of element
         */
        const handleClickOutside = (event: any) => {
            if (ref.current && !ref.current.contains(event.target) && !search_ref?.current.contains(event.target)) {
                set_courses(null);
                set_rule_id(null);
                retract();
                set_open(false);
            }
        }
        // Bind the event listener
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            // Unbind the event listener on clean up
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [ref]);
}

const Trigger = styled.div`
  
`


export const ExpandedCoursesPanelTrigger = ({ courses, triggerType, changeExpandIcon, ruleId, searchRef, children }: PropsWithChildren<{ courses: Fulfillment[], triggerType: "click" | "hover" | undefined, changeExpandIcon: () => void, ruleId: number, searchRef: MutableRefObject<any> }>) => {
    const ref = useRef<HTMLDivElement>(null);
    const { setPosition, set_courses, retract, set_retract, open, set_open, set_rule_id, set_search_ref } = useContext(ExpandedCoursesPanelContext);
    const timer = useRef<NodeJS.Timeout | null>(null);

    const showExpandedCourses = () => {
        if (!!open) {
            set_courses(null);
            set_open(false);
            set_rule_id(null);
            retract();
        } else {
            set_open(!open);
            set_courses(courses);
            set_retract(() => changeExpandIcon);
            set_rule_id(ruleId);
            set_search_ref(searchRef);
            if (!ref.current) return;
            const position: ExpandedCoursesPanelContextType["position"] = {}
            const { left, top, right, bottom } = searchRef.current.getBoundingClientRect();

            // calculate the optimal position
            let vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
            let vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
            if (left > (vw - right)) position["right"] = vw - left + 5; // set the right edge of the ExpandedCourses panel to left edge of trigger
            else position["left"] = right - 5;
            if (top > (vh - bottom)) position["bottom"] = vh - bottom;
            else position["top"] = top;

            setPosition(position);
        }
    }

    return (
        <Trigger
            ref={ref}
            onMouseEnter={() => {
                if (triggerType === "hover") {
                    timer.current = setTimeout(showExpandedCourses, REVIEWPANEL_TRIGGER_TIME)
                }
            }}
            onClick={showExpandedCourses}
            className="review-panel-trigger"
        >
            {children}
        </Trigger>
    )
}
interface ExpandedCoursesPanelContextType {
    position: { top?: number, bottom?: number, left?: number, right?: number };
    setPosition: (arg0: ExpandedCoursesPanelContextType["position"]) => void;
    courses: Fulfillment[] | null | undefined;
    set_courses: (arg0: Fulfillment[] | null | undefined) => void;
    retract: (() => void);
    set_retract: ((arg0: () => void) => void),
    open: boolean,
    set_open: ((arg0: boolean) => void),
    rule_id: number | null,
    set_rule_id: (arg0: number | null) => void,
    search_ref: MutableRefObject<any> | null,
    set_search_ref: (arg0: MutableRefObject<any> | null) => void,
    degree_plan_id: number | undefined
}

export const ExpandedCoursesPanelContext = createContext<ExpandedCoursesPanelContextType>({
    position: { top: 0, left: 0 },
    setPosition: (arg0) => { }, // placeholder
    courses: null,
    set_courses: (courses) => { }, // placeholder
    retract: () => { }, // placehoder 
    set_retract: (arg0) => { }, // placeholder
    open: false,
    set_open: (arg0) => { }, // placeholder
    rule_id: null,
    set_rule_id: (arg0) => { },
    search_ref: null,
    set_search_ref: (arg0) => { },
    degree_plan_id: undefined

});

interface ExpandedCoursesPanelProps extends ExpandedCoursesPanelContextType {
    currentSemester?: string;
}

const ExpandedCoursesPanelWrapper = styled.div<{ $left?: number, $right?: number, $top?: number, $bottom?: number, $isDroppable: boolean, $isOver: boolean }>`
    position: absolute;
    z-index: 100;
    max-height: 25vh;
    width: 25rem;
    overflow-x: hidden;
    border-radius: 10px;
    ${props => props.$left ? `left: ${props.$left}px;` : ""}
    ${props => props.$right ? `right: ${props.$right}px;` : ""}
    ${props => props.$top ? `top: ${props.$top}px;` : ""}
    ${props => props.$bottom ? `bottom: ${props.$bottom}px;` : ""}
    box-shadow: ${props => props.$isOver ? '0px 0px 4px 2px var(--selected-color);' : props.$isDroppable ? '0px 0px 4px 2px var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'};
    // box-shadow: 0 0 0 max(100vh, 100vw) rgba(0, 0, 0, .2);
`

const ExpandedCoursesPanelContainer = styled.div`
    background-color: var(--primary-color-light);
    overflow: auto;
    height: 100%;
`

const ExpandedCourses = styled.div`
    display: flex;
    flex-direction: column;
    gap: .5rem;
    cursor: pointer;
    padding: .5rem .75rem;
    height: 100%;
    gap: .5rem;
    padding: 1rem;

`

const EmptyExpandedText = styled.div`
    display: flex;
    height: 5rem;
    padding: 0 2rem;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: var(--primary-color-extra-dark);
`

const ExpandedCoursesHeader = styled.div`
    font-weight: bold;
`

const CourseList = styled.div`
    // flex-grow: 1;
    gap: .5rem;
    display: grid;
    grid-template-columns: auto auto;
`

const ExpandedCoursesPanel = ({
    courses,
    set_courses,
    position,
    setPosition,
    currentSemester,
    retract,
    set_open,
    rule_id,
    search_ref,
    set_search_ref,
    degree_plan_id
}: ExpandedCoursesPanelProps) => {
    let { left, right, top, bottom } = position;
    if (!left && !right) left = 0;
    if (!top && !bottom) right = 0;
    right = left === undefined ? right : undefined;
    bottom = top === undefined ? bottom : undefined;
    const wrapperRef = useRef(null);
    useOutsideAlerter(wrapperRef, retract, set_open);

    // hooks for LEAFs
    const { createOrUpdate } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${degree_plan_id}/fulfillments`,
        {
            idKey: "full_code",
            createDefaultOptimisticData: { semester: null, rules: [] }
        });

    const [{ isOver, canDrop }, drop] = useDrop<DnDCourse, never, { isOver: boolean, canDrop: boolean }>({
        accept: [ItemTypes.COURSE_IN_REQ],
        drop: (course: DnDCourse) => {
            if (rule_id) {
                course.rules?.splice(course.rules?.indexOf(rule_id), 1)
                createOrUpdate({ rules: course.rules !== undefined ? course.rules : [], unselected_rules: course.unselected_rules !== undefined ? [...course.unselected_rules, rule_id] : [rule_id] }, course.full_code);
            }

            if (courses && course.fulfillment) {
                set_courses([...courses, course.fulfillment])
            }

            return undefined;
        }, // TODO: this doesn't handle fulfillments that already have a rule
        canDrop: (course: DnDCourse) => {
            return rule_id === course.rule_id
        },
        collect: monitor => {
            return ({
                isOver: !!monitor.isOver(),
                canDrop: !!monitor.canDrop()
            })
        },
    }, [createOrUpdate]);

    return (

        <ExpandedCoursesPanelWrapper $right={right} $left={left} $top={top} $bottom={bottom} $isDroppable={canDrop} $isOver={isOver} ref={drop}>
            <ExpandedCoursesPanelContainer ref={wrapperRef}>
                <ExpandedCourses>
                    <ExpandedCoursesHeader>
                        Also satisfied by...
                    </ExpandedCoursesHeader>
                    {courses && courses?.length > 0 ?
                        <CourseList>
                            {courses?.map(fulfillment => (
                                <CourseInExpanded course={fulfillment} rule_id={rule_id ? rule_id : 0} fulfillment={fulfillment} isDisabled={false} activeDegreePlanId={fulfillment.degree_plan} />
                            ))}
                        </CourseList>
                        :
                        <EmptyExpandedText>
                            Drag any extra courses here that you don't want to use for this requirement.                        
                        </EmptyExpandedText>
                    }

                </ExpandedCourses>
            </ExpandedCoursesPanelContainer>
        </ExpandedCoursesPanelWrapper>
    )
}

export default ExpandedCoursesPanel;