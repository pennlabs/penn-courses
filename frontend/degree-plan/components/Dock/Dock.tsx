
import styled from '@emotion/styled';
import { DarkGrayIcon } from '../Requirements/QObject';
import React, { useContext, useEffect } from "react";
import { useDrag, useDrop } from "react-dnd";
import { Course, IDockedCourse } from "@/types";
import { ItemTypes } from "../dnd/constants";
import DockedCourse from './DockedCourse';
import { SearchPanelContext } from '../Search/SearchPanel';
import { useSWRCrud } from '@/hooks/swrcrud';
import useSWR, { useSWRConfig } from 'swr';


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
    justify-content: left;
    padding: 1rem 1rem;
`

const Divider = styled.div`
    height: 100%;
    width: 2px;
    background-color: grey;
    margin: 0px 15px;
`

const DockerElm = styled.div`
    
`
const SearchIconContainer = styled.div`
    margin: 1.5vh 1vh;
`

const DockedCoursesWrapper = styled.div`
    height: 100%;
    width: 100%;
    border-radius: 8px;
`

const DockedCourses = styled.div`
    height: 100%;
    display: flex;
    flex-direction: row;
    gap: 1rem;
    padding: 0.1rem;
`
const Dock = () => {
    const { setSearchPanelOpen, setSearchRuleQuery, setSearchRuleId } = useContext(SearchPanelContext)
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

    return (
        <DockWrapper ref={drop} >
            <DockContainer $isDroppable={canDrop} $isOver={isOver}>
                <DockerElm>
                    <SearchIconContainer onClick={() => {
                        setSearchRuleQuery(""); // TODO: should this reset the search?
                        setSearchRuleId(null);
                        setSearchPanelOpen(true);
                    }}>
                        <DarkGrayIcon>
                        <i className="fas fa-search fa-lg"/>
                        </DarkGrayIcon>
                    </SearchIconContainer>
                </DockerElm>
                <Divider/>
                <DockedCoursesWrapper>
                    {!isLoading && <DockedCourses>
                        {dockedCourses.map((full_code, i) => 
                            <DockedCourse removeDockedCourse={removeDockedCourse} full_code={full_code}/>
                        )}
                    </DockedCourses>}
                </DockedCoursesWrapper>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;