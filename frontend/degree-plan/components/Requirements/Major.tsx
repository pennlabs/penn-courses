import Rule from "./Rule"
import Icon from '@mdi/react';
import { mdiTrashCanOutline } from '@mdi/js';
import { mdiReorderHorizontal } from '@mdi/js';
import { mdiTriangleSmallDown, mdiTriangleSmallUp } from '@mdi/js';
import { useEffect, useRef, useState } from "react";
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { margin } from "@mui/system";
import { titleStyle } from "../FourYearPlan/SwitchFromList";
// import { titleStyle } from "@/pages/FourYearPlanPage";

const majorTitleStyle = {
    'borderWeight': 5
}

const Major = ({major, setSearchClosed}: any) => {
    const [collapsed, setCollapsed] = useState(true);
    return(
            <div className="m-2 ms-3 me-3">
                <div className='col-12'  style={{
                    backgroundColor:'#EDF1FC', 
                    fontSize:'16px', 
                    padding:'5px', 
                    paddingLeft:'10px', 
                    borderRadius:'10px',
                  }}>
                    <div>
                        <label className="d-flex justify-content-between">
                            <div style={titleStyle}>{major.name}</div>
                            <Icon path={collapsed ? mdiTriangleSmallDown : mdiTriangleSmallUp} size={1} />
                        </label>
                    </div>
                </div>
                {!collapsed &&
                <div className='ms-2 mt-2'>
                    {major.requirements.map((requirement: any) => ( <Rule key={requirement.id} requirement={requirement} setSearchClosed={setSearchClosed}/>))}
                </div>}
            </div>
    )
}

export default Major;