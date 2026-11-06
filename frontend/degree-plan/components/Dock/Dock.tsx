
import styled from '@emotion/styled';
import React, { useCallback, useContext, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useDrop } from "react-dnd";
import { DegreePlan, DnDCourse, DockedCourse, User } from "@/types";
import { ItemTypes } from "./dnd/constants";
import { SearchPanelContext } from '../Search/SearchPanel';
import { useSWRCrud } from '@/hooks/swrcrud';
import useSWR from 'swr';
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
import _ from 'lodash';
import CourseInDock from './CourseInDock';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { COURSE_LIST_ANIMATION } from '@/constants';

const DockWrapper = styled.div`
    z-index: 1;
    width: 100%;
    display: flex;
    justify-content: center;
    flex-grow: 0;
`

const COLLAPSED_HEIGHT = 66;
const MAX_HEIGHT = 320;
const COURSE_GAP = 16; // must match the courses' 1rem column gap
const ROW_GAP = 12;
const VERTICAL_PADDING = 32;

const DockContainer = styled.div<{$isDroppable:boolean, $isOver: boolean, $isExpanded: boolean}>`
    position: relative;
    box-sizing: border-box;
    overflow: hidden;
    border-radius: 0px;
    box-shadow: 0px 0px 4px 2px ${props => props.$isOver ? 'var(--selected-color);' : props.$isDroppable ? 'var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
    background-color: var(--primary-color);
    width: 100%;
    display: flex;
    align-items: ${props => props.$isExpanded ? 'flex-start' : 'center'};
    padding: 1rem 1rem;
    gap: 1rem;
    transition: box-shadow 150ms ease-out;
`

const ResizeHandle = styled.div`
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    z-index: 2;
    height: 10px;
    cursor: ns-resize;
    touch-action: none;

    &::before {
        content: "";
        position: absolute;
        top: 4px;
        left: 50%;
        transform: translateX(-50%);
        width: 2.5rem;
        height: 3px;
        border-radius: 2px;
        background: var(--primary-color-xx-dark);
        opacity: 0.45;
        transition: opacity 120ms ease;
    }

    &:hover::before {
        opacity: 0.9;
    }
`

const AddCourseButton = styled.button`
    display: flex;
    flex-shrink: 0;
    align-self: center;
    align-items: center;
    gap: 1rem;
    padding: .25rem 2rem .25rem 0;
    border: none;
    border-right: 2px solid var(--primary-color-xx-dark);
    background: none;
    color: var(--primary-color-ultra-dark);
    font-family: inherit;
    font-size: 1rem;
    white-space: nowrap;
    cursor: pointer;

    i {
        color: var(--primary-color-xxx-dark);
        font-size: 1.333rem;
    }

    &:hover i {
        color: var(--primary-color-ultra-dark);
    }
`

const DockedCoursesWrapper = styled.div<{ $isExpanded: boolean }>`
    height: 100%;
    align-self: stretch;
    width: 100%;
    border-radius: 8px;
    display: flex;
    align-items: center;
    flex-grow: 1;
    flex-shrink: 1;
    min-width: 0;
    overflow-x: ${props => props.$isExpanded ? 'hidden' : 'auto'};
    overflow-y: ${props => props.$isExpanded ? 'auto' : 'hidden'};

    /* Hide scrollbar */
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
    /* Hide scrollbar for Chrome, Safari and Opera */

    &::-webkit-scrollbar {
        display: none;
        height: 100px;
        width: 100px;
    }
`

const DockedCourses = styled.div<{ $isExpanded: boolean }>`
    min-height: 100%;
    flex-grow: 1;
    display: flex;
    flex-direction: row;
    flex-wrap: ${props => props.$isExpanded ? 'wrap' : 'nowrap'};
    align-items: ${props => props.$isExpanded ? 'flex-start' : 'center'};
    align-content: flex-start;
    gap: ${ROW_GAP}px ${COURSE_GAP}px;
    padding: 0.1rem;
`

const CenteringCourseDock = styled.div`
    color: var(--primary-color-extra-dark);
    margin-left: auto;
    margin-right: auto;
    align-self: center;
`

const DockedCourseItem = styled(CourseInDock)`
    z-index: 1000;
    background: var(--background-grey);
` 

interface DockProps {
    user: User | null;
    activeDegreeplanId: DegreePlan["id"] | null;
}

const Dock = ({ user, activeDegreeplanId  }: DockProps) => {
    const { searchPanelOpen, setSearchPanelOpen, setSearchRuleQuery, setSearchRuleId } = useContext(SearchPanelContext)
    const { createOrUpdate } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });
    const { data: dockedCourses = [], isLoading } = useSWR<DockedCourse[]>(user ? `/api/degree/docked` : null); 

    // Returns a boolean that indiates whether this is the first render
    const useIsMount = () => {
        const isMountRef = React.useRef(true);
        useEffect(() => {
          isMountRef.current = false;
        }, []);
        return isMountRef.current;
      };
    
    const [{ isOver, canDrop }, drop] = useDrop(() => ({
        accept: [ItemTypes.COURSE_IN_PLAN, ItemTypes.COURSE_IN_REQ, ItemTypes.COURSE_IN_SEARCH],
        drop: (course: DnDCourse) => {
           createOrUpdate({"full_code": course.full_code}, course.full_code);
        },
        collect: monitor => ({
          isOver: !!monitor.isOver(),
          canDrop: !!monitor.canDrop()
        }),
    }), []);

    const [animatedCourses] = useAutoAnimate(COURSE_LIST_ANIMATION);

    // Simulates the wrap from the courses' widths, so it doesn't depend on whether the dock is currently wrapping.
    const coursesRef = useRef<HTMLDivElement | null>(null);
    const setCoursesRef = useCallback((node: HTMLDivElement | null) => {
        coursesRef.current = node;
        animatedCourses(node);
    }, [animatedCourses]);
    const [fullHeight, setFullHeight] = useState(COLLAPSED_HEIGHT);
    const [height, setHeight] = useState(COLLAPSED_HEIGHT);
    const measure = useCallback(() => {
        const strip = coursesRef.current;
        const courses = strip ? [...strip.children] as HTMLElement[] : [];
        // The strip grows to fit its courses when they don't wrap, so measure the space it has.
        const width = strip?.parentElement?.clientWidth ?? 0;
        if (!dockedCourses.length || !courses.length || width <= 0) {
            setFullHeight(COLLAPSED_HEIGHT);
            return;
        }
        let rowWidth = 0;
        let rowHeight = 0;
        let total = 0;
        for (const course of courses) {
            if (rowWidth > 0 && rowWidth + course.offsetWidth > width) {
                total += rowHeight + ROW_GAP;
                rowWidth = 0;
                rowHeight = 0;
            }
            rowWidth += course.offsetWidth + COURSE_GAP;
            rowHeight = Math.max(rowHeight, course.offsetHeight);
        }
        total += rowHeight;
        setFullHeight(Math.min(MAX_HEIGHT, Math.max(COLLAPSED_HEIGHT, VERTICAL_PADDING + total + 4)));
    }, [dockedCourses]);

    useLayoutEffect(() => {
        const frame = requestAnimationFrame(measure);
        return () => cancelAnimationFrame(frame);
    }, [measure]);
    useEffect(() => {
        window.addEventListener("resize", measure);
        return () => window.removeEventListener("resize", measure);
    }, [measure]);
    useEffect(() => {
        setHeight((current) => Math.min(current, fullHeight));
    }, [fullHeight]);

    const canExpand = fullHeight > COLLAPSED_HEIGHT + 8;
    const isExpanded = height > COLLAPSED_HEIGHT + 8;

    const startResize = (e: React.PointerEvent) => {
        e.preventDefault();
        const startY = e.clientY;
        const startHeight = height;
        const move = (event: PointerEvent) => {
            const next = startHeight + (startY - event.clientY);
            setHeight(Math.min(fullHeight, Math.max(COLLAPSED_HEIGHT, next)));
        };
        const stop = () => {
            document.body.style.removeProperty("cursor");
            document.body.style.removeProperty("user-select");
            window.removeEventListener("pointermove", move);
            window.removeEventListener("pointerup", stop);
            window.removeEventListener("pointercancel", stop);
        };
        document.body.style.cursor = "ns-resize";
        document.body.style.userSelect = "none";
        window.addEventListener("pointermove", move);
        window.addEventListener("pointerup", stop);
        window.addEventListener("pointercancel", stop);
    };

    return (
        <DockWrapper ref={drop} >
            <DockContainer
                $isDroppable={canDrop}
                $isOver={isOver}
                $isExpanded={isExpanded}
                style={{ height }}
            >
                {canExpand && (
                    <ResizeHandle
                        role="separator"
                        aria-orientation="horizontal"
                        aria-label="Resize dock"
                        title="Drag to show more courses"
                        onPointerDown={startResize}
                    />
                )}
                <AddCourseButton type="button" onClick={() => {
                    setSearchRuleQuery("");
                    setSearchRuleId(null);
                    setSearchPanelOpen(!searchPanelOpen);
                }}>
                    <i className="fas fa-plus-circle" aria-hidden />
                    Add Course
                </AddCourseButton>
                <DockedCoursesWrapper $isExpanded={isExpanded}>
                    {isLoading ?
                    <CenteringCourseDock>
                        <DarkBlueBackgroundSkeleton width="20rem"/>
                    </CenteringCourseDock> 
                    :
                        <DockedCourses
                            $isExpanded={isExpanded}
                            ref={setCoursesRef}
                        >
                            {!dockedCourses.length && <CenteringCourseDock>Drop courses in the dock for later.</CenteringCourseDock>}
                            {dockedCourses.map((course) => 
                                <DockedCourseItem key={course.full_code} course={course} isDisabled={false} />
                            )}
                        </DockedCourses>}
                </DockedCoursesWrapper>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;