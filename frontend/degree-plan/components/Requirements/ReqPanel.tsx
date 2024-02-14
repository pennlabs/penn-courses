import { useEffect, useState } from 'react';
import SelectListDropdown from '../FourYearPlan/SelectListDropdown';
import Rule from './Requirement';
import { Degree, DegreePlan } from '@/types';
import styled from '@emotion/styled';
import { PanelBody, PanelContainer, PanelHeader } from '@/components/FourYearPlan/PlanPanel'
import { useSWRCrud } from '@/hooks/swrcrud';

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

 const temp = {
  "id": 42630,
  "rules": [
      {
          "id": 42631,
          "rules": [],
          "title": "Theory and Poetics",
          "num": null,
          "credits": 1.0,
          "q": "<Q: (AND: ('code__gte', 0), ('code__lte', 5999), ('department__code', 'ENGL'), ('attributes__code__in', ['AETP']))>",
          "parent": 42630
      },
      {
          "id": 42632,
          "rules": [],
          "title": "Difference and Diaspora",
          "num": null,
          "credits": 1.0,
          "q": "<Q: (AND: ('code__gte', 0), ('code__lte', 5999), ('department__code', 'ENGL'), ('attributes__code__in', ['AEDD']))>",
          "parent": 42630
      },
      {
          "id": 42633,
          "rules": [],
          "title": "Medieval/Renaissance",
          "num": null,
          "credits": 1.0,
          "q": "<Q: (AND: ('code__gte', 0), ('code__lte', 5999), ('department__code', 'ENGL'), ('attributes__code__in', ['AEMR']))>",
          "parent": 42630
      },
      {
          "id": 42634,
          "rules": [],
          "title": "Literature of the Long 18th Century",
          "num": null,
          "credits": 1.0,
          "q": "<Q: (OR: ('full_code', 'ENGL-0022'), ('full_code', 'ENGL-0521'), ('full_code', 'ENGL-1330'), ('full_code', 'ENGL-1800'), ('full_code', 'ENGL-2030'), ('full_code', 'ENGL-2321'), (AND: ('code__gte', 0), ('code__lte', 5999), ('department__code', 'ENGL'), ('attributes__code__in', ['AE18'])))>",
          "parent": 42630
      },
      {
          "id": 42635,
          "rules": [],
          "title": "19th Century Literature",
          "num": null,
          "credits": 1.0,
          "q": "<Q: (AND: ('code__gte', 0), ('code__lte', 5999), ('department__code', 'ENGL'), ('attributes__code__in', ['AE19']))>",
          "parent": 42630
      },
      {
          "id": 42636,
          "rules": [],
          "title": "20th Century Literature",
          "num": null,
          "credits": 1.0,
          "q": "<Q: (AND: ('code__gte', 0), ('code__lte', 5999), ('department__code', 'ENGL'), ('attributes__code__in', ['AE20']))>",
          "parent": 42630
      }
  ],
  "title": "THE CORE",
  "num": null,
  "credits": null,
  "q": "",
  "parent": 42629
}
const ReqPanel = ({activeDegreePlan, isLoading, highlightReqId, setSearchClosed, handleSearch, setHighlightReqId}: ReqPanelProps) => {
  const degrees = activeDegreePlan?.degrees;
  const [activeDegreeId, setActiveDegreeId] = useState<Degree["id"] | undefined>(undefined);
  const [activeDegree, setActiveDegree] = useState<Degree | undefined>(undefined);
  
  // useEffect(() => {
  //   if (!activeDegreeId && degrees?.length) {
  //     setActiveDegreeId(degrees[0].id);
  //   }
  // }, [activeDegreeId, activeDegreePlan])

  useEffect(() => {
    if (activeDegreeId && degrees) {
      console.log("aha")
      console.log(degrees);
      setActiveDegree(degrees.find(degree => degree.id === activeDegreeId));
    }
  }, [activeDegreeId])

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
          {temp.rules.map((rule: any) => ( 
              <Rule rule={rule} setSearchClosed={setSearchClosed} handleSearch={handleSearch} setHighlightReqId={setHighlightReqId} highlightReqId={highlightReqId} key={rule.id}/>
            ))
            || <EmptyPanel />
            }
        </PanelBody>
      </PanelContainer>
  );
}
export default ReqPanel;