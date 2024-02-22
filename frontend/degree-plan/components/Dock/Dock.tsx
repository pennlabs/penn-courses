
import styled from '@emotion/styled';
import { DarkGrayIcon } from '../Requirements/QObject';
import React, { useContext } from "react";
import { useDrag, useDrop } from "react-dnd";
import { Course } from "@/types";
import { ItemTypes } from "../dnd/constants";
import DockedCourse from './DockedCourse';
import { SearchPanelContext } from '../Search/SearchPanel';


const DockWrapper = styled.div`
    opacity: 0.9;
    width: 100%;
    display: flex;
    justify-content: center;
`

const DockContainer = styled.div<{$isDroppable:boolean, $isOver: boolean}>`
    border-radius: 15px;
    box-shadow: 0px 0px 4px 2px ${props => props.$isOver ? 'var(--selected-color);' : props.$isDroppable ? 'var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
    background-color: var(--primary-color-light);
    height: 5vh;
    min-width: 28vw;
    display: flex;
    justify-content: left;
    padding: 5px 10px;
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
// border-style: solid;
// border-color: grey;

const DockedCourses = styled.div`
    display: flex;
    flex-direction: row;
`
const Dock = () => {
    const { setSearchPanelOpen, setSearchRuleQuery, setSearchRuleId } = useContext(SearchPanelContext)
    const [dockedCourses, setDockedCourses] = React.useState<string[]>([]);

    const removeDockedCourse = (full_code: string) => {
        setDockedCourses((dockedCourses) => dockedCourses.filter(c => c !== full_code));
    }

    const [{ isOver, canDrop }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (course: Course) => {
            console.log("DROPPED", course.full_code, 'from', course.semester);
            setDockedCourses((dockedCourses) => dockedCourses.filter(c => c !== course.full_code)); // to prevent duplicates
            setDockedCourses((dockedCourses) => [...dockedCourses, course.full_code]);
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
                        <i className="fas fa-search fa-lg" />
                        </DarkGrayIcon>
                    </SearchIconContainer>
                </DockerElm>
                <Divider/>
                    <DockedCoursesWrapper>
                        <DockedCourses >
                            {dockedCourses.map((full_code, i) => 
                                <DockedCourse removeDockedCourse={removeDockedCourse} full_code={full_code}/>
                            )}
                        </DockedCourses>
                    </DockedCoursesWrapper>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;