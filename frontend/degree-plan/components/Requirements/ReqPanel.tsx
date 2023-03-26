import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft } from '@mdi/js';
import majorsdata from '../../data/majors';
import Major from './Major';
import { useCallback, useEffect, useState } from 'react';
import update from 'immutability-helper'

export const reqPanelContainerStyle = {
    // backgroundColor: '#FFFFFF', 
    boxShadow: '0px 0px 10px 6px rgba(0, 0, 0, 0.05)', 
    borderRadius: '10px',
    width: 400,
    height: '100%',
    backgroundColor: '#FFFFFF'
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
          <div className="" style={{backgroundColor:'#DBE2F5', paddingLeft: '15px', paddingTop: '3px', paddingBottom: '2px', paddingRight: '15px', borderTopLeftRadius: '10px', borderTopRightRadius: '10px'}}>
              <div className='m-2 d-flex justify-content-between'>
                <div style={{color: '#575757', fontWeight: 'bold'}}>Major/Minor/Elective</div>
                <label onClick={() => setEditMode(!editMode)}>
                    <Icon path={editMode ? mdiArrowLeft : mdiNoteEditOutline } size={1}/>
                </label>
              </div>
          </div>
          <div style={{padding:'1rem'}}>
              {/** header of requirements section */}

              {/** majors */}
              <div className='m-1' style={{maxHeight:'570px', overflow: 'auto'}}>
                  {majors.map((major, index) => <Major key={index} index={index} major={major} editMode={editMode} moveMajor={moveMajor}/>)}
              </div>
          </div>
        </div>
    );
}
export default ReqPanel;