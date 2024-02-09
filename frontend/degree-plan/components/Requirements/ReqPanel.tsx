import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft, mdiPlus } from '@mdi/js';
import { useEffect, useState } from 'react';
import { topBarStyle } from '@/pages/FourYearPlanPage';
import SelectListDropdown from '../FourYearPlan/SelectListDropdown';
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
              <Requirement requirement={requirement} setSearchClosed={setSearchClosed} parent={null} handleSearch={handleSearch} setHighlightReqId={setHighlightReqId} highlightReqId={highlightReqId} key={requirement.id}/>
            ))}
          </div>
        </>
    );
}
export default ReqPanel;