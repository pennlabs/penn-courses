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
  
  const ReqPanel = ({majors, currentMajor, highlightReqId, setCurrentMajor, setMajors, setSearchClosed, setDegreeModalOpen, handleSearch, setHighlightReqId}:any) => {
      const [editMode, setEditMode] = useState(false);
      const [majorData, setMajorData] = useState({});
      // useEffect(() => {
      //   setMajor(majorsdata[0]);
      // }, [currentMajorStr])

      // useEffect(() => {
      //   const getAllMajors = async () => {
      //     setMajors([{id: 1, name: 'PPE (BSE)'}, {id: 2, name: 'Visual Studies (BAS)'}]);
      //     setCurrentMajor({id: 1, name: 'PPE (BSE)'});
      //   }
      //   getAllMajors();
      // }, [])

      useEffect(() => {
        const getMajor = async () => {
            const res = await axios.get(`/degree/degrees/${currentMajor.id}`);
            console.log(res.data);
            setMajorData(res.data);
            return;
        }
        if (currentMajor.id) getMajor();
      }, [currentMajor])

    return(
        <>
          <div style={topBarStyle}>
              <div className='d-flex justify-content-between'>
              <SwitchFromList
                  current={currentMajor} 
                  setCurrent={setCurrentMajor}
                  list={majors} 
                  setList={setMajors} 
                  addHandler={() => setDegreeModalOpen(true)}/>
                <label onClick={() => setEditMode(!editMode)}>
                    <Icon path={editMode ? mdiArrowLeft : mdiNoteEditOutline } size={1}/>
                </label>
              </div>
          </div>
          <div style={requirementDropdownListStyle}>
            {majorData && majorData.rules && majorData.rules.map((requirement: any) => ( 
              <Requirement requirement={requirement} setSearchClosed={setSearchClosed} parent={null} handleSearch={handleSearch} setHighlightReqId={setHighlightReqId} highlightReqId={highlightReqId}/>
            ))}
          </div>
        </>
    );
}
export default ReqPanel;