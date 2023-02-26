import Requirement from "./Requirement"
import Icon from '@mdi/react';
import { mdiTrashCanOutline } from '@mdi/js';
import { mdiReorderHorizontal } from '@mdi/js';
import { mdiTriangleSmallDown, mdiTriangleSmallUp } from '@mdi/js';
import { useEffect, useRef, useState } from "react";
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";

const majorTitleStyle = {
    'borderWeight': 5
}

const Major = ({major, editMode, index, moveMajor}: any) => {
    const [collapsed, setCollapsed] = useState(false);
    // const [canDrag, setCanDrag] = useState(editMode);
    let ref = useRef<HTMLInputElement>(null);

    // useEffect(() => {
    //     setCanDrag(editMode);
    //     console.log(canDrag);
    // }, [editMode]);

    const [{ handlerId }, drop] = useDrop(
        () => ({
          accept: ItemTypes.MAJOR,
          collect: (monitor) => ({
            isOver: !!monitor.isOver(),
            handlerId: monitor.getHandlerId()
          }),
          hover(item: any, monitor) {
            if (!ref.current) {
              return
            }
            const dragIndex = item.index
            const hoverIndex = index
            // Don't replace items with themselves
            if (dragIndex === hoverIndex) {
              return
            }
            // Determine rectangle on screen
            const hoverBoundingRect = ref.current?.getBoundingClientRect()
            // Get vertical middle
            const hoverMiddleY =
              (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2
            // Determine mouse position
            const clientOffset = monitor.getClientOffset()
            // Get pixels to the top
            const hoverClientY = clientOffset!.y - hoverBoundingRect.top
            // Only perform the move when the mouse has crossed half of the items height
            // When dragging downwards, only move when the cursor is below 50%
            // When dragging upwards, only move when the cursor is above 50%
            // Dragging downwards
            if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
              return
            }
            // Dragging upwards
            if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
              return
            }
            // Time to actually perform the action
            moveMajor(dragIndex, hoverIndex)
            // Note: we're mutating the monitor item here!
            // Generally it's better to avoid mutations,
            // but it's good here for the sake of performance
            // to avoid expensive index searches.
            item.index = hoverIndex
          }
        }),
        []
      )
    /** React dnd */
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.MAJOR,
        item: () => {
            return { index }
          },
        canDrag: editMode,
        collect: (monitor) => ({
          isDragging: false // editMode && !!monitor.isDragging(),
        })
      }),[editMode])
      
    const handleCollapse = () => {
        /** can only collapse/expand when not in edit mode */
        if (!editMode) 
        setCollapsed(!collapsed);
    }

    /** if in edit mode, collapse by default, else expand by default */
    useEffect(() => {
        if (editMode) setCollapsed(true);
        else setCollapsed(false);
    }, [editMode])

    drag(drop(ref))
    return(
        <>  
            <div
                ref={ref}
                style={{
                    opacity: isDragging ? 0.5 : 1,
                    cursor: 'move',
                }}
                >
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