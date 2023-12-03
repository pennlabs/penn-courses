import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft } from '@mdi/js';
import majorsdata from '../../data/majors';
import Major from './Major';
import { useCallback, useEffect, useState } from 'react';
import update from 'immutability-helper'
import { Stack } from '@mui/material';
import { titleStyle, topBarStyle } from '@/pages/FourYearPlanPage';
import SearchPanel from '../Search/SearchPanel';

const majorStackStyle = {
  height: '90%',
  overflow: 'auto'
}
  
  const ReqPanel = ({setSearchClosed}:any) => {
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
        <>
          <div style={topBarStyle}>
              <div className='d-flex justify-content-between'>
                <div style={titleStyle}>Major/Minor/Elective</div>
                <label onClick={() => setEditMode(!editMode)}>
                    <Icon path={editMode ? mdiArrowLeft : mdiNoteEditOutline } size={1}/>
                </label>
              </div>
          </div>
          <div style={majorStackStyle}>
              {/** majors */}
                  {majors.map((major, index) => <Major key={index} index={index} major={major} editMode={editMode} moveMajor={moveMajor} setSearchClosed={setSearchClosed}/>)}
          </div>
        </>
    );
}
export default ReqPanel;