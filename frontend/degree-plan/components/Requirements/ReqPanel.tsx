import { useCallback, useEffect, useMemo, useState } from 'react';
import RuleComponent from './Rule';
import { Degree, DegreePlan, Fulfillment, Rule } from '@/types';
import styled from '@emotion/styled';
import { EditButton, PanelBody, PanelContainer, PanelHeader, PanelTopBarIcon, PanelTopBarIconList, TopBarIcon } from '@/components/FourYearPlan/PlanPanel'
import { useSWRCrud } from '@/hooks/swrcrud';
import useSWR from 'swr';
import { GrayIcon, Icon } from '../common/bulma_derived_components';
import React from 'react';

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
  font-size: 1rem;
  font-weight: 500;
  background-color: var(--primary-color);
  padding: 0.5rem 1rem;
  border-radius: var(--req-item-radius);
`

const ReqPanelTitle = styled.div`
  font-size: 1.5rem;
  font-weight: 500;
`

const DegreeBody = styled.div`
  padding: 0.5rem 1rem;
  overflow-y: auto;
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
export const TrashIcon = styled(GrayIcon)`
  pointer-events: auto;
  color: #b2b2b2;
  &:hover {
    color: #7E7E7E;
  }
`

const AddButton = styled.div`
  width: 100%;
  display: flex;
  flex-direction: row;
  gap: 1rem;
  justify-content: center;
  background-color: var(--plus-button-color);
  padding: 1rem;
  border-radius: var(--req-item-radius);
  align-items: center;
  color: white;
`

const DegreeHeader = ({ degree, remove, setCollapsed, collapsed, editMode }: { degree: Degree, remove: (degreeId: Degree["id"]) => void, setCollapsed: (status: boolean) => void, collapsed: boolean, editMode: boolean}) => {
  const degreeName = `${degree.degree} in ${degree.major} ${degree.concentration ? `(${degree.concentration})` : ''}`
  return (
    <DegreeHeaderContainer onClick={() => setCollapsed(!collapsed)}>
      <DegreeTitleWrapper>
        <div>
          {degreeName}
        </div>
        <DegreeYear>
          {degree.year}
        </DegreeYear>
      </DegreeTitleWrapper>
      <span>
        {!!editMode ? 
        <TrashIcon role="button" onClick={() => remove(degree.id)}>
          <i className="fa fa-trash fa-md"/>
        </TrashIcon>
        :
        <Icon>
          <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
        </Icon>}
      </span>
    </DegreeHeaderContainer>
  )
}

const Degree = ({degree, rulesToFulfillments, activeDegreeplan, editMode, setModalKey, setModalObject}: any) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div>
      <DegreeHeader 
      degree={degree} 
      key={degree.id} 
      remove={() => {
        setModalObject(activeDegreeplan);
        setModalKey("degree-remove");
      }} 
      setCollapsed={setCollapsed}
      collapsed={collapsed || editMode} // Collapse degree view in edit mode
      editMode={editMode}
      />
      {!collapsed && !editMode &&
      <DegreeBody>
        {degree.rules.map((rule: any) => (
          <RuleComponent 
          rulesToFulfillments={rulesToFulfillments}
          activeDegreePlanId={activeDegreeplan.id}
          rule={rule} 
          key={rule.id}
          />
        ))}
      </DegreeBody>}
    </div>
  )
}

interface ReqPanelProps {
  setModalKey: (arg0: string) => void;
  setModalObject: (arg0: DegreePlan | null) => void;
  activeDegreeplan: DegreePlan | null;
  isLoading: boolean;
  setSearchClosed: any;
  handleSearch: any;
}
const ReqPanel = ({setModalKey, setModalObject, activeDegreeplan, isLoading, setSearchClosed, handleSearch}: ReqPanelProps) => {
  const [editMode, setEditMode] = React.useState(false);

  const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<Fulfillment[]>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments` : null); 

  const rulesToFulfillments = useMemo(() => {
    if (!fulfillments) return {}
    const rulesToCourses: { [rule: string]: Fulfillment[] } = {};
    fulfillments.forEach(fulfillment => {
      fulfillment.rules.forEach(rule => {
        if (!(rule in rulesToCourses)) {
          rulesToCourses[rule] = [];
        }
        rulesToCourses[rule].push(fulfillment);
      });
    });
    // console.log(rulesToCourses)
    return rulesToCourses;
  }, [fulfillments])

  const getProgress = (rule: any) => {
    if (rule.q) {
      return [rulesToFulfillments[rule.id].length, rule.num] // rule.num is not the most accurate rep of number of reqs
    }
    let satisfied = 0, total = 0;
    for (let i = 0; i < rule.rules.length; i++) {
      const [satisfiedByRule, totalByRule] = getProgress(rule.rules[i]);
      satisfied += satisfiedByRule; total += totalByRule;
    }
    return [satisfied, total];
  } 

  return(
      <PanelContainer>
        <PanelHeader>
          <ReqPanelTitle>Requirements</ReqPanelTitle>
          <PanelTopBarIconList>
            <EditButton editMode={editMode} setEditMode={setEditMode} />
          </PanelTopBarIconList>
        </PanelHeader>
        {!activeDegreeplan ? <EmptyPanel /> :
          <PanelBody>
            {activeDegreeplan.degrees.map(degree => (
              <Degree 
              degree={degree} 
              rulesToFulfillments={rulesToFulfillments} 
              activeDegreeplan={activeDegreeplan} 
              setSearchClosed={setSearchClosed} 
              handleSearch={handleSearch}
              editMode={editMode}
              setModalKey={setModalKey}
              setModalObject={setModalObject}
              />
            ))}
            {editMode && 
            <AddButton role="button" onClick={() => {
              setModalObject(activeDegreeplan);
              setModalKey("degree-add");
            }}>
              <i className="fa fa-plus" />
              <div>
                Add Degree
              </div>
            </AddButton>}
        </PanelBody>
        }
      </PanelContainer>
  );
}
export default ReqPanel;