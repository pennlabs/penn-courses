import React, { useState } from "react";
import { useDrop } from 'react-dnd';
import { useDispatch} from 'react-redux';
import { courseAddedToSemester } from "../../store/reducers/courses";
import { semesterCourseList } from "../../styles/FourYearStyles";
import CourseInCart from "../Cart/CourseInCart";
import { ISemester, ICourse } from "../../store/configureStore";
import CoursePlanned from "./CoursePlanned";
import { DragDropContext, Draggable, DraggableProvided, Droppable, DroppableProvided, DropResult } from 'react-beautiful-dnd';


import {
    DndContext, 
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    useDroppable,
  } from '@dnd-kit/core';
  import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
  } from '@dnd-kit/sortable';

// interface SemesterProps {
//     year: string,
//     semester: ISemester
// }

const semesterCardStyle = {
    background: 'linear-gradient(0deg, #FFFFFF, #FFFFFF), #FFFFFF',
    boxShadow: '0px 0px 4px 2px rgba(0, 0, 0, 0.05)',
    borderRadius: '10px',
    borderWidth: '0px',
    padding: '15px'
}
const Semester = ({semester, items, id, index} : any) => {

    const [courses, setCourses] = useState(semester.courses);
    console.log(items);
    const { setNodeRef } = useDroppable({
        id
    });

    return (
        <>
            <div className="card col-5 m-3" style={semesterCardStyle}>
                <h5 className="mt-1 mb-1">
                    {semester.name}
                </h5>
                    <SortableContext 
                        items={items[index]}
                        strategy={verticalListSortingStrategy}
                    >
                        <div ref={setNodeRef}> 
                        {items[index].map((id: string) => 
                            <CoursePlanned courses={courses} id={id} key={id}/>
                        )}
                        </div>
                    </SortableContext>
                    {/* </div>
                </SortableContext> */}
            </div>
        </>
    )
}

export default Semester;