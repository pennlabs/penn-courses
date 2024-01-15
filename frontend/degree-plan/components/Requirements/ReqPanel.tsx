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
import axios from 'axios';

const requirementDropdownListStyle = {
  maxHeight: '90%',
  width: '100%',
  overflowY: 'scroll',
  paddingRight: '15px',
  paddingLeft: '15px',
  marginTop: '10px'
}
  
  const ReqPanel = ({setSearchClosed, setDegreeModalOpen, handleSearch}:any) => {
      const [editMode, setEditMode] = useState(false);
      const [majorStrs, setMajorStrs] = useState([]);
      const [currentMajorStr, setCurrentMajorStr] = useState(majorStrs[0]);
      const [major, setMajor] = useState({});

      // useEffect(() => {
      //   setMajor(majorsdata[0]);
      // }, [currentMajorStr])

      useEffect(() => {
        const getAllMajors = async () => {
          setMajorStrs(['Computer Science, BSE', 'English, BAS']);
          setCurrentMajorStr('Computer Science, BSE');
        }
        getAllMajors();
      }, [])

      useEffect(() => {
        const getMajor = async () => {
            const res = await axios.get('/degree/degree_detail/1');
            console.log(res.data);
            setMajor(res.data);
            return;
        }
        getMajor();
      }, [currentMajorStr])

    return(
        <>
          <div style={topBarStyle}>
              <div className='d-flex justify-content-between'>
              <SwitchFromList
                  current={currentMajorStr} 
                  setCurrent={setCurrentMajorStr}
                  list={majorStrs} 
                  setList={setMajorStrs} 
                  addHandler={() => setDegreeModalOpen(true)}/>
                <label onClick={() => setEditMode(!editMode)}>
                    <Icon path={editMode ? mdiArrowLeft : mdiNoteEditOutline } size={1}/>
                </label>
              </div>
          </div>
          <div style={requirementDropdownListStyle}>
            {major && major.rules && major.rules.map((requirement: any) => ( 
              <Requirement requirement={requirement} setSearchClosed={setSearchClosed} parent={null} handleSearch={handleSearch}/>
            ))}
          </div>
        </>
    );
}
export default ReqPanel;