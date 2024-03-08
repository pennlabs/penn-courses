
import styled from '@emotion/styled';
import { DarkBlueIcon } from '../Requirements/QObject';
import React, { useContext, useEffect } from "react";
import { useDrop } from "react-dnd";
import { Course, IDockedCourse, User } from "@/types";
import { ItemTypes } from "../dnd/constants";
import DockedCourse from './DockedCourse';
import { SearchPanelContext } from '../Search/SearchPanel';
import { useSWRCrud } from '@/hooks/swrcrud';
import useSWR, { useSWRConfig } from 'swr';
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";

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
    border-color: var(--primary-color-extra-dark);
    border-width: 0;
    border-right-width: 2px;
    border-style: solid;
    flex-shrink: 0;
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

interface DockProps {
    login: (u: User) => void;
    logout: () => void;
    user: User | null;
}
const Dock = ({ user, login, logout  }: DockProps) => {
    const { searchPanelOpen, setSearchPanelOpen, setSearchRuleQuery, setSearchRuleId } = useContext(SearchPanelContext)
    const [dockedCourses, setDockedCourses] = React.useState<string[]>([]);
    const { createOrUpdate,remove } = useSWRCrud<IDockedCourse>(`/api/degree/docked`, {idKey: 'full_code'});
    const {data: dockedCourseObjs, isLoading} = useSWR<IDockedCourse[]>(`/api/degree/docked`, {fallback: []}) 

    const removeDockedCourse = async (full_code: string) => {
        /** Preemtively update frontend */
        setDockedCourses((dockedCourses) => dockedCourses.filter(c => c !== full_code));
        /** Update backend */
        await remove(full_code);
    }

    useEffect(() => {
        if (dockedCourseObjs !== undefined) {
            setDockedCourses(dockedCourseObjs.map(obj => obj.full_code));
        }
    }, [dockedCourseObjs])

    const [{ isOver, canDrop }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (course: Course) => {
            console.log("DROPPED", course.full_code, 'from', course.semester);
            const repeated = dockedCourses.filter(c => c === course.full_code)
            if (!repeated.length) {
                /** Preemtively update frontend */
                setDockedCourses((dockedCourses) => [...dockedCourses, course.full_code]);
                /** Update backend */
                createOrUpdate({"full_code": course.full_code}, course.full_code);
            }
        },
        canDrop: () => {return true},
        collect: monitor => ({
          isOver: !!monitor.isOver(),
          canDrop: !!monitor.canDrop()
        }),
    }), []);

    const dockedCoursesComponent = isLoading ?
        <CenteringCourseDock>
            <DarkBlueBackgroundSkeleton width="20rem"/>
        </CenteringCourseDock> 
         :
        !dockedCourses.length ? <CenteringCourseDock>Drop courses in the dock for later.</CenteringCourseDock> :
        <DockedCourses>
            {dockedCourses.map((full_code, i) => 
                <DockedCourse removeDockedCourse={removeDockedCourse} full_code={full_code}/>
            )}
        </DockedCourses>

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
                />
                <SearchIconContainer onClick={() => {
                    setSearchRuleQuery("");
                    setSearchRuleId(null);
                    setSearchPanelOpen(!searchPanelOpen);
                }}>
                    <DarkBlueIcon>
                        <i className="fas fa-search fa-lg"/>
                    </DarkBlueIcon>
                </SearchIconContainer>
                <DockedCoursesWrapper>
                    {dockedCoursesComponent}
                </DockedCoursesWrapper>
                <Logo src='pdp-logo.svg' width='30' height='45'/>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;