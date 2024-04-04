import { useMemo, useState } from 'react';
import RuleComponent, { SkeletonRule } from './Rule';
import { Degree as DegreeType, DegreePlan, Fulfillment, Rule } from '@/types';
import styled from '@emotion/styled';
import { DarkBlueBackgroundSkeleton, PanelBody, PanelContainer, PanelHeader, PanelTopBarIconList } from "../FourYearPlan/PanelCommon";
import { EditButton } from '../FourYearPlan/EditButton';
import useSWR from 'swr';
import { Icon } from '../common/bulma_derived_components';
import React from 'react';
import { ModalKey } from '../FourYearPlan/DegreeModal';
import { LightTrashIcon } from '../common/TrashIcon';

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
  background-color: var(--primary-color-xx-dark);
  color: #FFF;
  padding: 0.75rem 1.25rem;
  border-radius: var(--req-item-radius);
`

const ReqPanelTitle = styled.div`
  font-size: 1.25rem;
  font-weight: 500; 
`

const DegreeBody = styled.div`
  margin-top: .5rem;
  overflow-y: auto;
  overflow-x: hidden;
`

export const DegreeYear = styled.span`
  margin-left: .25rem;
  font-size: .9rem;
  font-weight: 500;
`
const  DegreeTitleWrapper = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: .5rem;
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

const ReqPanelBody = styled(PanelBody)`
  overflow-y: scroll;
  padding: .75rem;
`

interface DegreeHeaderProps {
  degree: DegreeType,
  remove: (degreeId: DegreeType["id"]) => void,
  setCollapsed: (status: boolean) => void,
  collapsed: boolean,
  editMode: boolean,
  skeleton?: boolean,
}

const DegreeHeader = ({ degree, remove, setCollapsed, collapsed, editMode, skeleton }: DegreeHeaderProps) => {
  const degreeName = !skeleton ? `${degree.degree} in ${degree.major_name} ${degree.concentration ? `(${degree.concentration_name})` : ''}` : <DarkBlueBackgroundSkeleton width="10em" />;
  return (
    <DegreeHeaderContainer onClick={() => setCollapsed(!collapsed)}>
      <DegreeTitleWrapper>
        <div>
          {degreeName}
        </div>
        <DegreeYear>
          {!skeleton ? degree.year : <DarkBlueBackgroundSkeleton width="4em" />}
        </DegreeYear>
      </DegreeTitleWrapper>
      <span>
        {!skeleton && !!editMode ? 
        <LightTrashIcon role="button" onClick={() => remove(degree.id)}>
          <i className="fa fa-trash fa-md"/>
        </LightTrashIcon>
        :
        <Icon>
          <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
        </Icon>}
      </span>
    </DegreeHeaderContainer>
  )
}


// Logic for rule trees
interface RuleTreeBaseNode {
  type: string;
  rule: Rule;
  activeDegreePlanId: DegreePlan["id"];
  progress: number; // a number between 0 and 1
}
interface RuleTreeLeaf extends RuleTreeBaseNode {
  type: "LEAF";
  cus: number;
  num: number;
  fulfillments: Fulfillment[]; // The fulfillments for the rule
}
interface RuleTreeInternalNode extends RuleTreeBaseNode {
  type: "INTERNAL_NODE";
  num?: number;
  children: RuleTree[];
}
export type RuleTree = RuleTreeLeaf | RuleTreeInternalNode;

// TODO: factor out activeDegreePlanId so it's not in entire tree
interface RuleProps {
    rule: Rule;
    rulesToFulfillments: { [ruleId: string]: Fulfillment[] };
    activeDegreePlanId: number;
}
const computeRuleTree = ({ activeDegreePlanId, rule, rulesToFulfillments }: RuleProps): RuleTree => {
  if (rule.q) { // Rule leaf
    const fulfillmentsForRule: Fulfillment[] = rulesToFulfillments[rule.id] || [];
    const cus = fulfillmentsForRule.reduce((acc, f) => acc + (f.course?.credits || 1), 0); // default to 1 cu 
    const num = fulfillmentsForRule.length;
    const progress = Math.min(rule.credits ? cus / rule.credits : 1, rule.num ? num / rule.num : 1);
    return { activeDegreePlanId, type: "LEAF", progress, cus, num, rule, fulfillments: fulfillmentsForRule }
  }
  
  const children = rule.rules.map((child) => computeRuleTree({ activeDegreePlanId, rule: child, rulesToFulfillments })) 
  const progress = children.reduce((acc, { progress }) => (progress == 1 ? 1 : 0) + acc, 0) / Math.min(children.length, rule.num || Infinity);
  return { num: rule.num || undefined, activeDegreePlanId, type: "INTERNAL_NODE", children, progress, rule } // internal node
}


const Degree = ({degree, rulesToFulfillments, activeDegreeplan, editMode, setModalKey, setModalObject, isLoading}: any) => {
  const [collapsed, setCollapsed] = useState(false);  
  if (isLoading) {
    return (
      <div>
        <DegreeHeader
        degree={degree}
        remove={() => void {}}
        setCollapsed={setCollapsed}
        skeleton
        collapsed={collapsed}
        editMode={false}
        />
        <DegreeBody>
          <SkeletonRule>
            <SkeletonRule>
              <SkeletonRule />
              <SkeletonRule />
              {/* <SkeletonRule /> */}
            </SkeletonRule>
            <SkeletonRule>
              <SkeletonRule />
              {/* <SkeletonRule />
              <SkeletonRule /> */}
            </SkeletonRule>
          </SkeletonRule>
          <SkeletonRule>
            <SkeletonRule />
            <SkeletonRule />
            <SkeletonRule />
          </SkeletonRule>
        </DegreeBody>
      </div>
    )
  }

  return (
    <div>
      <DegreeHeader 
        degree={degree} 
        key={degree.id} 
        remove={() => {
          setModalObject({degreeplanId: activeDegreeplan.id, degreeId: degree.id});
          setModalKey("degree-remove");
        }} 
        setCollapsed={setCollapsed}
        collapsed={collapsed || editMode} // Collapse degree view in edit mode
        editMode={editMode}
        skeleton={false}
        />
      {!collapsed && !editMode &&
      <DegreeBody>
        {degree && degree.rules.map((rule: any) => (
          <RuleComponent 
          {...computeRuleTree({ activeDegreePlanId: activeDegreeplan.id, rule, rulesToFulfillments })}
          />
        ))}
      </DegreeBody>}
    </div>
  )
}

interface ReqPanelProps {
  setModalKey: (arg0: ModalKey) => void;
  setModalObject: (arg0: DegreePlan | null) => void;
  activeDegreeplan: DegreePlan | null;
  isLoading: boolean;
}
const ReqPanel = ({setModalKey, setModalObject, activeDegreeplan, isLoading}: ReqPanelProps) => {
  const [editMode, setEditMode] = React.useState(false);  
  const { data: activeDegreeplanDetail = null, isLoading: isLoadingDegrees } = useSWR<DegreePlan>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}` : null); 
  const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<Fulfillment[]>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments` : null); 

  const rulesToFulfillments = useMemo(() => {
    if (isLoadingFulfillments || !fulfillments) return {};
    const rulesToCourses: { [rule: string]: Fulfillment[] } = {};
    fulfillments.forEach(fulfillment => {
      fulfillment.rules.forEach(rule => {
        if (!(rule in rulesToCourses)) {
          rulesToCourses[rule] = [];
        }
        rulesToCourses[rule].push(fulfillment);
      });
    });
    return rulesToCourses;
  }, [fulfillments, isLoadingFulfillments])
  
  return(
    <PanelContainer>
      <PanelHeader>
        <ReqPanelTitle>Requirements</ReqPanelTitle>
        <PanelTopBarIconList>
          <EditButton editMode={editMode} setEditMode={setEditMode} />
        </PanelTopBarIconList>
      </PanelHeader>
      {!activeDegreeplan ? <ReqPanelBody><Degree isLoading={true}/></ReqPanelBody> :
      <>
        {activeDegreeplanDetail && 
        <ReqPanelBody>
          {activeDegreeplanDetail.degrees.length == 0 && !editMode && <EmptyPanel />}
          {activeDegreeplanDetail.degrees.map(degree => (
            <Degree 
            degree={degree} 
            rulesToFulfillments={rulesToFulfillments} 
            activeDegreeplan={activeDegreeplan}
            editMode={editMode}
            setModalKey={setModalKey}
            setModalObject={setModalObject}
            isLoading={isLoading}
            />
          ))}
          {editMode && <AddButton role="button" onClick={() => {
            setModalObject(activeDegreeplan);
            setModalKey("degree-add");
          }}>
            <i className="fa fa-plus" />
            <div>
              Add Degree
            </div>
          </AddButton>}
        </ReqPanelBody>
        }
      </>}
    </PanelContainer>
  );
}
export default ReqPanel;
