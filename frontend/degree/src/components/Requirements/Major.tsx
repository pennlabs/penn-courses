import Requirement from "./Requirement"
import Icon from '@mdi/react';
import { mdiTrashCanOutline } from '@mdi/js';
import { mdiReorderHorizontal } from '@mdi/js';
import { mdiTriangleSmallDown, mdiTriangleSmallUp } from '@mdi/js';
import { useEffect, useState } from "react";
import { DragDropContext, Draggable, DraggableProvided, Droppable, DroppableProvided, DropResult } from 'react-beautiful-dnd';

import {CSS} from '@dnd-kit/utilities';
import {useSortable} from '@dnd-kit/sortable';

const majorTitleStyle = {
    'borderWeight': 5
}

const Major = ({major, editMode, id}: any) => {
    const [collapsed, setCollapsed] = useState(false);

    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
      } = useSortable({id: id});

      
      
      const handleCollapse = () => {
          /** can only collapse/expand when not in edit mode */
          if (!editMode) 
          setCollapsed(!collapsed);
        }

        const style = {
            transform: CSS.Transform.toString(transform),
            transition
          };

    /** if in edit mode, collapse by default, else expand by default */
    useEffect(() => {
        if (editMode) setCollapsed(true);
        else setCollapsed(false);
    }, [editMode])

    return(
        <>  
            <div ref={setNodeRef} style={style} {...attributes} {...listeners}  >
                <label className='col-12'>
                    <div style={{backgroundColor:"#DBE2F5", padding:'5px', paddingLeft:'10px', borderRadius:'12px'}}>
                        <label onMouseDown={handleCollapse} className="d-flex justify-content-between">
                            <div style={{borderWidth:'5px'}}>{major.name}</div>
                            {editMode ? 
                                <label>
                                    <Icon path={mdiTrashCanOutline} size={0.92} />
                                    <Icon path={mdiReorderHorizontal} size={0.92} />
                                </label> :
                                    <Icon path={collapsed ? mdiTriangleSmallDown : mdiTriangleSmallUp} size={1} />
                                }
                        </label>
                    </div>
                    <div className='m-2'>
                        {major.reqs.map((req: any) => (!collapsed && <Requirement req={req}/>))}
                    </div>
                </label>
            </div>
                
        </>
    )
}

export default Major;