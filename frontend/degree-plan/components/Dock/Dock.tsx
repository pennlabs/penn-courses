
import styled from '@emotion/styled';
import { DarkGrayIcon } from '../Requirements/QObject';
import React from "react";
import { useDrop } from "react-dnd";
import { Course } from "@/types";
import { ItemTypes } from "../dnd/constants";
import { CourseID, CourseIDContainer } from '../Search/Course';
import { BaseCourseContainer, RemoveCourseButton } from '../FourYearPlan/CoursePlanned';
import { GrayIcon } from '../bulma_derived_components';


const DockWrapper = styled.div`
    z-index: 1;
    opacity: 0.9;
    position: fixed;
    width: 100%;
    bottom: 2%;
    display: flex;
    justify-content: center;
`

const DockContainer = styled.div`
    border-radius: 15px;
    background-color: var(--primary-color-dark);
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

const DockedCourse = styled.div`
    margin: 1px;
    position: relative;
`

interface IDock {
    setSearchClosed: (status: boolean) => void;
    setReqId: (id: number) => void;
}

const Dock = ({setSearchClosed, setReqId}: IDock) => {
    // const ref = React.useRef(null);
    const [dockedCourses, setDockedCourses] = React.useState<string[]>([]);
    const [mouseOver, setMouseOver] = React.useState(false);

    const removeCourse = (full_code: string) => {
        setDockedCourses((dockedCourses) => dockedCourses.filter(c => c !== full_code));
    }

    const [{ isOver }, drop] = useDrop(() => ({
        accept: ItemTypes.COURSE,
        drop: (course: Course) => {
            console.log("DROPPED", course.full_code, 'from', course.semester);
            setDockedCourses((dockedCourses) => dockedCourses.filter(c => c !== course.full_code)); // to prevent duplicates
            setDockedCourses((dockedCourses) => [...dockedCourses, course.full_code]);
        },
        collect: monitor => ({
          isOver: !!monitor.isOver()
        }),
    }), []);

    return (
        <DockWrapper>
            <DockContainer>
                <DockerElm>
                    <SearchIconContainer onClick={() => {setSearchClosed(false); setReqId(-1);}}>
                        <DarkGrayIcon>
                        <i class="fas fa-search fa-lg"/>
                        </DarkGrayIcon>
                    </SearchIconContainer>
                </DockerElm>
                <Divider/>
                <DockedCoursesWrapper ref={drop}>
                    <DockedCourses >
                        {dockedCourses.map((full_code, i) => 
                            <DockedCourse 
                                key={i}     
                                onMouseOver={() => setMouseOver(true)} 
                                onMouseLeave={() => setMouseOver(false)}>
                                <BaseCourseContainer>
                                    <span>{full_code.replace(/-/g, " ")}</span>
                                    <RemoveCourseButton hidden={!mouseOver} onClick={() => removeCourse(full_code)}>
                                        <GrayIcon><i className="fas fa-times"></i></GrayIcon>
                                    </RemoveCourseButton>
                                </BaseCourseContainer>
                            </DockedCourse>
                        )}
                    </DockedCourses>
                </DockedCoursesWrapper>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;