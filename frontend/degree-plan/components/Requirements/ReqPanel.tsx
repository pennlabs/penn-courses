import Icon from '@mdi/react';
import { mdiNoteEditOutline, mdiArrowLeft, mdiPlus } from '@mdi/js';
import { useEffect, useState } from 'react';
import { PanelTopBar } from '@/pages/FourYearPlanPage';
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
            // const res = await axios.get(`/degree/degrees/${currentMajor.id}`);
            // console.log(res.data);
            // setMajorData(res.data);
            // return;
        }
        if (currentMajor.id) getMajor();
      }, [currentMajor])

    return(
        <>
          <PanelTopBar>
              <SelectListDropdown 
              allItems={[]}
              active={undefined}
              selectItem={setCurrentMajor}
              itemType={"major or degree"}
              mutators={{
                copy: () => {},
                remove: () => {},
                rename: () => {},
                create: () => {}
              }}
              />
          </PanelTopBar>
          <div style={requirementDropdownListStyle}>
            {majorData && majorData.rules && majorData.rules.map((requirement: any) => ( 
              <Requirement requirement={requirement} setSearchClosed={setSearchClosed} parent={null} handleSearch={handleSearch} setHighlightReqId={setHighlightReqId} highlightReqId={highlightReqId} key={requirement.id}/>
            ))}
          </div>
        </>
    );
}
export default ReqPanel;