import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft } from '@mdi/js';
import { CartPanel } from '../../styles/CartStyles';
import majorsdata from '../../data/majors';
import Major from './Major';
import { useEffect, useState } from 'react';
import { DragDropContext, Draggable, DraggableProvided, Droppable, DroppableProvided, DropResult } from 'react-beautiful-dnd';

import {
    DndContext, 
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
  } from '@dnd-kit/core';
  import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    verticalListSortingStrategy,
  } from '@dnd-kit/sortable';



export const reqPanelContainerStyle = {
    border: '1px solid rgba(0, 0, 0, 0.1)',
    padding: '1rem',
    borderRadius: '4px',
    height: 650,
    width: 400
  }

const ReqPanel = () => {
    const [editMode, setEditMode] = useState(false);
    const [majors, setMajors] = useState(majorsdata);
    const [items, setItems] = useState([1, 2, 3, 4]);

    const switchOrder = (source_index: any, destination_index: any) => {
        const temp = majors[source_index];
        majors[source_index] = majors[destination_index];
        majors[destination_index] = temp;
    }

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
              distance: 5,
            },
          }),
        useSensor(KeyboardSensor, {
          coordinateGetter: sortableKeyboardCoordinates,
        })
      );

    const handleDragEnd = (event: any) => {
        const {active, over} = event;
    
        if (active.id !== over.id) {
            setItems((items) => {
                const oldIndex = items.indexOf(active.id);
                const newIndex = items.indexOf(over.id);
                
                return arrayMove(items, oldIndex, newIndex);
            });
        }
    }

    useEffect(() => {
        setMajors(majorsdata);
    }, []);

    return(
        <div style={reqPanelContainerStyle}>
            {/** header of requirements section */}
            <div className="d-flex justify-content-between">
                <h5>Major/Minor/Elective</h5>
                <label onClick={() => setEditMode(!editMode)}>
                    <Icon path={editMode ? mdiArrowLeft : mdiNoteEditOutline } size={1}/>
                </label>
            </div>

            {/** majors */}
            <div className='m-2' style={{maxHeight:'570px', overflow: 'auto'}}>
                <DndContext 
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                    >
                    <SortableContext 
                        items={items}
                        strategy={verticalListSortingStrategy}
                    >
                        {items.map(id => <Major key={id} id={id} major={majors[id - 1]} editMode={editMode}/>)}
                    </SortableContext>
                </DndContext>
            </div>
        </div>
    );
}
export default ReqPanel;