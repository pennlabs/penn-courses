import Requirement from "./Requirement"
import Icon from '@mdi/react';
import { mdiTrashCanOutline } from '@mdi/js';
import { mdiReorderHorizontal } from '@mdi/js';
import { mdiTriangleSmallDown, mdiTriangleSmallUp } from '@mdi/js';
import { useEffect, useRef, useState } from "react";
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { margin } from "@mui/system";
import { titleStyle } from "@/pages/FourYearPlanPage";

const majorTitleStyle = {
    'borderWeight': 5
}

const Major = ({major, editMode, index, moveMajor, setSearchClosed}: any) => {
    const [collapsed, setCollapsed] = useState(false);
    let ref = useRef<HTMLInputElement>(null);

    const [{ opacity }, drop] = useDrop(
        () => ({
          accept: ItemTypes.MAJOR,
          collect: (monitor) => ({
            opacity: !!monitor.isOver() ? 0 : 1
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
            // Time to actually perform the action
            moveMajor(dragIndex, hoverIndex)
            // mutate the monitor item for the sake of performance to avoid expensive index searches
            item.index = hoverIndex
          }
        }),
        []
      )
    /** React dnd */
    const [{ isDragging}, drag] = useDrag(() => ({
        type: ItemTypes.MAJOR,
        item: () => {
            return { index }
          },
        canDrag: editMode,
        collect: (monitor) => ({
          isDragging: !!monitor.isDragging()
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
            <div className="m-3">
                <div className='col-12' ref={ref} style={{
                    opacity: opacity,
                    backgroundColor:'#EDF1FC', 
                    fontSize:'16px', 
                    padding:'5px', 
                    paddingLeft:'10px', 
                    borderRadius:'10px',
                  }}>
                    <div>
                        <label onMouseDown={handleCollapse} className="d-flex justify-content-between">
                            <div style={titleStyle}>{major.name}</div>
                            {editMode ? 
                                <label>
                                    <Icon path={mdiTrashCanOutline} size={0.92} />
                                    <Icon path={mdiReorderHorizontal} size={0.92} />
                                </label> :
                                    <Icon path={collapsed ? mdiTriangleSmallDown : mdiTriangleSmallUp} size={1} />
                                }
                        </label>
                    </div>
                </div>
                {!collapsed &&
                <div className='ms-2 mt-2'>
                    {major.requirements.map((requirement: any) => ( <Requirement key={requirement.id} requirement={requirement} setSearchClosed={setSearchClosed}/>))}
                </div>}
            </div>
        </>
    )
}

export default Major;