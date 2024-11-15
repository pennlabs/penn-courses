
import styled from '@emotion/styled';
import { DarkBlueIcon } from '../Requirements/QObject';
import React, { useContext, useEffect } from "react";
import { useDrop } from "react-dnd";
import { Course, DegreePlan, DnDCourse, DockedCourse, Fulfillment, User } from "@/types";
import { ItemTypes } from "../dnd/constants";
import { SearchPanelContext } from '../Search/SearchPanel';
import { useSWRCrud } from '@/hooks/swrcrud';
import useSWR, { useSWRConfig } from 'swr';
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
// TODO: Move shared components to typescript
// @ts-ignore
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import _ from 'lodash';
import CoursePlanned from '../FourYearPlan/CourseInPlan';
import CourseInDock from './CourseInDock';
import { useRouter } from 'next/router';

const DockWrapper = styled.div`
    z-index: 1;
    width: 100%;
    display: flex;
    justify-content: center;
    flex-grow: 0;
`

const DockContainer = styled.div<{$isDroppable:boolean, $isOver: boolean}>`
    border-radius: 0px;
    box-shadow: 0px 0px 4px 2px ${props => props.$isOver ? 'var(--selected-color);' : props.$isDroppable ? 'var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
    background-color: var(--primary-color);
    width: 100%;
    display: flex;
    align-items: center;
    padding: 1rem 1rem;
    gap: 1rem;
`

const SearchIconContainer = styled.div`
    padding: .25rem 2rem;
    padding-left: 0;
    border-color: var(--primary-color-xx-dark);
    color: var(--primary-color-extra-dark);
    border-width: 0;
    border-right-width: 2px;
    border-style: solid;
    flex-shrink: 0;
    display: flex;
    gap: 1rem;
`

const DockedCoursesWrapper = styled.div`
    height: 100%;
    width: 100%;
    border-radius: 8px;
    display: flex;
    align-items: center;
    flex-grow: 1;
    flex-shrink: 1;
    overflow-x: auto;

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

const DockedCourses = styled.div`
    height: 100%;
    display: flex;
    flex-direction: row;
    gap: 1rem;
    padding: 0.1rem;
    overflow: auto;
`

const CenteringCourseDock = styled.div`
    color: var(--primary-color-extra-dark);
    margin-left: auto;
    margin-right: auto;
`

const Logo = styled.img`
    flex-shrink: 0;
`

const AnimatedDockedCourseItem = styled(CourseInDock)`
    z-index: 1000;
    background: var(--background-grey);
    animation-name: jump;
      animation-duration: 1.5s;
      animation-iteration-count: 1;
      animation-timing-function: linear;
` 

interface DockProps {
    login: (u: User) => void;
    logout: () => void;
    user: User | null;
    activeDegreeplanId: DegreePlan["id"] | null;
}

const Dock = ({ user, login, logout, activeDegreeplanId  }: DockProps) => {
    // const [courseAdded, setCourseAdded] = React.useState(false);
    const { searchPanelOpen, setSearchPanelOpen, setSearchRuleQuery, setSearchRuleId } = useContext(SearchPanelContext)
    // const { createOrUpdate } = useSWRCrud<DockedCourse>(["DOCK", `/api/degree/docked`], { idKey: 'full_code' });
    const { createOrUpdate } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });
    const { data: dockedCourses = [], isLoading } = useSWR<DockedCourse[]>(user ? `/api/degree/docked` : null); 

    // console.log(dockedCourses)

    // Returns a boolean that indiates whether this is the first render
    const useIsMount = () => {
        const isMountRef = React.useRef(true);
        useEffect(() => {
          isMountRef.current = false;
        }, []);
        return isMountRef.current;
      };
    
    const [{ isOver, canDrop }, drop] = useDrop(() => ({
        accept: [ItemTypes.COURSE_IN_PLAN, ItemTypes.COURSE_IN_REQ],
        drop: (course: DnDCourse) => {
           createOrUpdate({"full_code": course.full_code}, course.full_code);
        },
        collect: monitor => ({
          isOver: !!monitor.isOver(),
          canDrop: !!monitor.canDrop()
        }),
    }), []);

    // React.useEffect(() => {
    //     if (!isMount) {
    //         console.log('future render');
    //         setCourseAdded(true);
    //         setTimeout(() => {
    //             setCourseAdded(false);
    //         }, 3000);
    //     } else {
    //         console.log('first render');
    //     }
    // }, [isMount, dockedCourses]);

    const { asPath } = useRouter();

    return (
        <DockWrapper ref={drop} >
            <DockContainer $isDroppable={canDrop} $isOver={isOver}>
                <AccountIndicator
                leftAligned={true}
                user={user}
                backgroundColor="light"
                nameLength={2}
                login={login}
                logout={logout}
                dropdownTop={true}
                pathname={asPath}
                />
                <SearchIconContainer onClick={() => {
                    setSearchRuleQuery("");
                    setSearchRuleId(null);
                    setSearchPanelOpen(!searchPanelOpen);
                }}>
                    <DarkBlueIcon>
                        <i className="fas fa-plus fa-lg"/>
                    </DarkBlueIcon>
                    <div>
                        Add Course
                    </div>
                </SearchIconContainer>
                <DockedCoursesWrapper>
                    {isLoading ?
                    <CenteringCourseDock>
                        <DarkBlueBackgroundSkeleton width="20rem"/>
                    </CenteringCourseDock> 
                    :
                    !dockedCourses.length ? <CenteringCourseDock>Drop courses in the dock for later.</CenteringCourseDock> :
                        // courseAdded ?
                        // <DockedCourses>
                        //     {dockedCourses.map((course, i) => {
                        //         if (i == dockedCourses.length - 1) {
                        //             return <AnimatedDockedCourseItem course={course} isUsed isDisabled={false} />
                        //         }
                        //         return <DockedCourseItem course={course} isUsed isDisabled={false} />
                        //     }
                        //     )}
                        // </DockedCourses>
                        // :
                        <DockedCourses>
                            {dockedCourses.map((course) => 
                                <AnimatedDockedCourseItem course={course} isDisabled={false} />
                            )}
                        </DockedCourses>}
                </DockedCoursesWrapper>
                <Logo src='pdp-logo.svg' width='30' height='45'/>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;