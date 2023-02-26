import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft } from '@mdi/js';
import majorsdata from '../../data/majors';
import Major from './Major';
import { useCallback, useEffect, useState } from 'react';
import update from 'immutability-helper'

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
      
      useEffect(() => {
          setMajors(majorsdata);
      }, []);

      const moveMajor = useCallback((dragIndex: number, hoverIndex: number) => {
        setMajors((prevMajors) =>
          update(prevMajors, {
            $splice: [
              [dragIndex, 1],
              [hoverIndex, 0, prevMajors[dragIndex]],
            ],
          }),
        )
      }, [])

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
                {majors.map((major, index) => <Major index={index} major={major} editMode={editMode} moveMajor={moveMajor}/>)}
            </div>
        </div>
    );
}
export default ReqPanel;