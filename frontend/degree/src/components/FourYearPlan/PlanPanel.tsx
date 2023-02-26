import { useEffect, useState } from "react";
import semestersData from "../../data/semesters";
import Semester from "./Semester";
import {
    DndContext, 
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragOverlay,
  } from '@dnd-kit/core';
  import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
  } from '@dnd-kit/sortable';
import CoursePlanned from "./CoursePlanned";

const planPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 800
  }
  const semesterCardStyle = {
    background: 'linear-gradient(0deg, #FFFFFF, #FFFFFF), #FFFFFF',
    boxShadow: '0px 0px 4px 2px rgba(0, 0, 0, 0.05)',
    borderRadius: '10px',
    borderWidth: '0px',
    padding: '15px'
}



const PlanPanel = () => {
    
    const [semesters, setSemesters] = useState(semestersData);
    // potential index: String.fromCharCode('A'.charCodeAt(0) + idx1)
    const [items, setItems] = useState(semestersData.map((sem, idx1) => sem.courses.map((c, idx2) => ""+idx1+idx2)));
    console.log(items);
    
    const sensors = useSensors(
      useSensor(PointerSensor),
      useSensor(KeyboardSensor, {
        coordinateGetter: sortableKeyboardCoordinates,
      })
    );

    const handleDragEnd = (event: any) => {
      const {active, over} = event;
      console.log(event);
      if (active.id !== over.id) {
          const fromSemesterId = parseInt(active.id[0]);
          const toSemesterId = parseInt(over.id[0]);
          if (fromSemesterId === toSemesterId) {
            setItems((items: any) => {
                const oldIndex = items[fromSemesterId].indexOf(active.id);
                const newIndex = items[fromSemesterId].indexOf(over.id);
                items[fromSemesterId] = arrayMove(items[fromSemesterId], oldIndex, newIndex);
                return items;
              });
            }
            console.log(items);
        }
  }

    return(
    <>
        <div style={planPanelContainerStyle}>
            {/* <Tabs/> */}
            {/** map to semesters */}
            <div className="d-flex row justify-content-center">
              {semesters.map((semester, index) => 
                  <DndContext 
                      sensors={sensors}
                      collisionDetection={closestCenter}
                      onDragEnd={handleDragEnd}
                      >
                      <Semester semester={semester} items={items} index={index}/>
                  </DndContext>
              )}
            </div>
        </div>
    </>);
}

export default PlanPanel;