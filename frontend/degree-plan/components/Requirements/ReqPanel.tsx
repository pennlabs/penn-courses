import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft, mdiPlus } from '@mdi/js';
import majorsdata from '../../data/majors';
import Major from './Major';
import { useCallback, useEffect, useState } from 'react';
import update from 'immutability-helper'
import { Stack } from '@mui/material';
import { topBarStyle } from '@/pages/FourYearPlanPage';
import SearchPanel from '../Search/SearchPanel';
import SwitchFromList from '../FourYearPlan/SwitchFromList';
import Requirement from './Requirement';

const majorStackStyle = {
  height: '90%',
  overflow: 'auto'
}
  
  const ReqPanel = ({setSearchClosed, setDegreeModalOpen}:any) => {
      const [editMode, setEditMode] = useState(false);
      const [majors, setMajors] = useState(['Computer Science, BSE', 'English, BAS']);
      const [currentMajorStr, setCurrentMajorStr] = useState(majors[0]);
      const [major, setMajor] = useState({});

      useEffect(() => {
        setMajor(majorsdata[0]);
      }, [currentMajorStr])

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
              <SwitchFromList
                  current={currentMajorStr} 
                  setCurrent={setCurrentMajorStr} 
                  list={majors} 
                  setList={setMajors} 
                  addHandler={() => setDegreeModalOpen(true)}/>
                <label onClick={() => setEditMode(!editMode)}>
                    <Icon path={editMode ? mdiArrowLeft : mdiNoteEditOutline } size={1}/>
                </label>
              </div>
          </div>
          <div className='m-3'>
            {major.requirements.map((requirement: any) => ( 
              <Requirement key={requirement.id} requirement={requirement} setSearchClosed={setSearchClosed}/>
            ))}
          </div>
        </>
    );
}
export default ReqPanel;