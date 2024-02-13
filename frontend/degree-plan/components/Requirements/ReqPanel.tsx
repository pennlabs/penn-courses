import { useEffect, useState } from 'react';
import SelectListDropdown from '../FourYearPlan/SelectListDropdown';
import Rule from './Requirement';
import { Degree, DegreePlan } from '@/types';
import styled from '@emotion/styled';
import { PanelBody, PanelContainer, PanelHeader } from '@/components/FourYearPlan/PlanPanel'
import { useSWRCrud } from '@/hooks/swrcrud';
import { set, update } from 'lodash';
import { useSWRConfig } from 'swr';

const requirementDropdownListStyle = {
  maxHeight: '90%',
  width: '100%',
  overflowY: 'auto',
  paddingRight: '15px',
  paddingLeft: '15px',
  marginTop: '10px'
}

const EmptyPanelContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 2rem;
  text-align: center;
`;

const EmptyPanelImage = styled.img`
    max-width: min(60%, 40vw);
`;

const EmptyPanel = () => {
  return (
    <EmptyPanelContainer>
      <EmptyPanelImage src="/images/empty-state-cal.svg" />
      There's nothing here so far... add a degree to get started!
    </EmptyPanelContainer>
  )
}

interface ReqPanelProps {
  activeDegreePlan: DegreePlan | null;
  isLoading: boolean;
}
const ReqPanel = ({activeDegreePlan, isLoading, highlightReqId, setSearchClosed, handleSearch, setHighlightReqId}: ReqPanelProps) => {
  const degrees = activeDegreePlan?.degrees;
  const [activeDegreeId, setActiveDegreeId] = useState<Degree["id"] | undefined>(undefined);
  const [activeDegree, setActiveDegree] = useState<Degree | undefined>(undefined);
  useEffect(() => {
    if (!activeDegreeId && degrees?.length) {
      setActiveDegreeId(degrees[0].id);
    }
  }, [activeDegreeId, activeDegreePlan])

  useEffect(() => {
    if (activeDegreeId && degrees) {
      setActiveDegree(degrees.find(degree => degree.id === activeDegreeId));
    }
  })

  const { update: updateDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
  
  return(
      <PanelContainer>
        <PanelHeader>
            <SelectListDropdown 
            allItems={degrees || []}
            active={activeDegree}
            selectItem={(id: Degree["id"]) => setActiveDegreeId(id)}
            getItemName={(degree: Degree) => `${degree.major}, ${degree.degree}`}
            itemType={"major or degree"}
            mutators={{
              remove: (degree) => {
                updateDegreeplan(
                  {degree_ids: activeDegreePlan?.degree_ids?.filter(id => id !== degree.id) || []},
                  activeDegreePlan?.id
                )
                if (degree.id === activeDegreeId) setActiveDegreeId(undefined);
              },
              create: () => updateDegreeplan(
                {degree_ids: [...(activeDegreePlan?.degree_ids || []), 1867]}, // TODO: this is a placeholder, we need to add a new degree
                activeDegreePlan?.id
              )?.then(() => setActiveDegreeId(1867)),
            }}
            />
        </PanelHeader>
        <PanelBody>
          {activeDegree?.rules?.map((rule: any) => ( 
              <Rule rule={rule} setSearchClosed={setSearchClosed} handleSearch={handleSearch} setHighlightReqId={setHighlightReqId} highlightReqId={highlightReqId} key={rule.id}/>
            ))
            || <EmptyPanel />
            }
        </PanelBody>
      </PanelContainer>
  );
}
export default ReqPanel;