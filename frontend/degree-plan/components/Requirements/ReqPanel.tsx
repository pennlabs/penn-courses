import { useMemo } from 'react';
import RuleComponent from './Rule';
import { Degree, DegreePlan, Fulfillment } from '@/types';
import styled from '@emotion/styled';
import { PanelBody, PanelContainer, PanelHeader } from '@/components/FourYearPlan/PlanPanel'
import { useSWRCrud } from '@/hooks/swrcrud';
import useSWR from 'swr';
import { GrayIcon } from '../common/bulma_derived_components';
import { AddButton } from '../FourYearPlan/Semesters';

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
  height: 80%;
  align-items: center;
  padding: 2rem;
  text-align: center;
`;

const EmptyPanelImage = styled.img`
    max-width: min(60%, 20rem);
`;

const EmptyPanel = () => {
  return (
    <EmptyPanelContainer>
      <EmptyPanelImage src="/images/empty-state-cal.svg" />
      There's nothing here so far... add a degree to get started!
    </EmptyPanelContainer>
  )
}

const DegreeHeaderContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.5rem;
  font-weight: 500;
`
const DegreeYear = styled.div`
  font-size: 1.25rem;
  font-weight: 500;
  color: #575757;
`
const DegreeTitleWrapper = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: .5rem;
`
const TrashIcon = styled(GrayIcon)`
  pointer-events: auto;
  color: #b2b2b2;
  &:hover {
    color: #7E7E7E;
  }
`

const DegreeWrapper = styled.div`
  margin-bottom: 1rem;
`

const DegreeHeader = ({ degree, remove }: { degree: Degree, remove: (degreeId: Degree["id"]) => void}) => {
  const degreeName = `${degree.degree} in ${degree.major} ${degree.concentration ? `(${degree.concentration})` : ''}`
  return (
    <DegreeHeaderContainer>
      <DegreeTitleWrapper>
        <div>
          {degreeName}
        </div>
        <DegreeYear>
          {degree.year}
        </DegreeYear>
      </DegreeTitleWrapper>
      <TrashIcon role="button" onClick={() => remove(degree.id)}>
        <i className="fa fa-trash fa-xs"/>
      </TrashIcon>
    </DegreeHeaderContainer>
  )
}

interface ReqPanelProps {
  setModalKey: (arg0: string) => void;
  setModalObject: (arg0: DegreePlan | null) => void;
  activeDegreeplan: DegreePlan | null;
  isLoading: boolean;
}
const ReqPanel = ({setModalKey, setModalObject, activeDegreeplan, isLoading, setSearchClosed, handleSearch}: ReqPanelProps) => {
  const degrees = activeDegreeplan?.degrees;
  const { update: updateDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
  
  const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<Fulfillment[]>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments` : null); 
  const rulesToFulfillments = useMemo(() => {
    if (!fulfillments) return {}
    const rulesToCourses: { [semester: string]: Fulfillment[] } = {};
    fulfillments.forEach(fulfillment => {
      fulfillment.rules.forEach(rule => {
        if (!(rule in rulesToCourses)) {
          rulesToCourses[rule] = [];
        }
        rulesToCourses[rule].push(fulfillment);
      });
    });
    return rulesToCourses;
  }, [fulfillments])

  return(
      <PanelContainer>
        <PanelBody>
            {!activeDegreeplan ? <EmptyPanel /> :
              activeDegreeplan.degrees.map(degree => (
                <DegreeWrapper>
                  <DegreeHeader degree={degree} key={degree.id} remove={(id) => {
                    setModalKey("degree-remove")
                    // TODO
                  }}/>
                  {degree.rules.map((rule: any) => (
                    <RuleComponent 
                    rulesToFulfillments={rulesToFulfillments}
                    rule={rule} 
                    setSearchClosed={setSearchClosed} 
                    handleSearch={handleSearch} 
                    key={rule.id}
                    />
                  ))}
                </DegreeWrapper>
              )) 
            }
            <AddButton role="button" onClick={() => {
              setModalObject(activeDegreeplan);
              setModalKey("degree-add");
            }}>
              <i className="fa fa-plus" />
              <div>
                Add Degree
              </div>
            </AddButton>
        </PanelBody>
      </PanelContainer>
  );
}
export default ReqPanel;