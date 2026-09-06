
import { useMemo, useState, useContext, useRef, useLayoutEffect } from 'react';
import RuleComponent, { SkeletonRule } from './Rule';
import { Degree as DegreeType, DegreePlan, Fulfillment, Rule, Degree as DegreeD } from '@/types';
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
  position: sticky;
  top: 0;
  z-index: 1000;
`

const ReqPanelTitle = styled.div`
  font-size: 1.25rem;
  font-weight: 700; 
`

const DegreeBody = styled.div`
  overflow-y: none;
`

export const DegreeYear = styled.span`
  margin-left: .25rem;
  font-size: .9rem;
  font-weight: 500;
`
const DegreeTitleWrapper = styled.div`
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
  padding: 1.5rem;
  gap: 0;
`

// pr, mr for scroll bar
const ReqContent = styled.div`
  padding: 0;
  padding-right: 12px;
  margin-right: -12px;
  display: flex;
  flex-direction: column;
  gap: .5rem;
  overflow-y: scroll;
`

export const HEADER_DEFAULT_BUFFER = 8;
export const WhiteSpace = styled.div<{ $headerHeight: number, $zIndex: number }>`
  height: ${HEADER_DEFAULT_BUFFER}px;
  background-color: white;
  z-index: ${(props) => props.$zIndex || 500};
  position: sticky;
  top: ${(props) => props.$headerHeight}px;
`

export interface PlanProgram {
  id: number;
  relation: "degrees" | "majors" | "minors";
  title: string;
  year: number;
  rules: Rule[];
}

const planPrograms = (detail: DegreePlan): PlanProgram[] => [
  ...(detail.degrees ?? []).map((degree) => ({
    id: degree.id,
    relation: "degrees" as const,
    title: `${degree.degree} in ${degree.major_name}${
      degree.concentration ? ` (${degree.concentration_name})` : ""
    }`,
    year: degree.year,
    rules: degree.rules,
  })),
  ...(detail.majors ?? []).map((major) => ({
    id: major.id,
    relation: "majors" as const,
    title: `Major in ${major.name}${
      major.concentration_name ? ` (${major.concentration_name})` : ""
    }`,
    year: major.year,
    rules: major.rules,
  })),
  ...(detail.minors ?? []).map((minor) => ({
    id: minor.id,
    relation: "minors" as const,
    title: `Minor in ${minor.name}`,
    year: minor.year,
    rules: minor.rules,
  })),
];

interface DegreeHeaderProps {
  program: PlanProgram,
  remove: (id: number) => void,
  setCollapsed: (status: boolean) => void,
  collapsed: boolean,
  editMode: boolean,
  skeleton?: boolean,
  containerRef?: React.Ref<HTMLDivElement>
}

const DegreeHeader = ({ 
  program, 
  remove, 
  setCollapsed, 
  collapsed, 
  editMode, 
  skeleton,
  containerRef
}: DegreeHeaderProps) => {
  const degreeName = !skeleton ? program.title : <DarkBlueBackgroundSkeleton width="10em" />;
  return (
    <DegreeHeaderContainer ref={containerRef} onClick={() => setCollapsed(!collapsed)}>
      <DegreeTitleWrapper>
        <div>
          {degreeName}
        </div>
        <DegreeYear>
          {!skeleton ? program.year : <DarkBlueBackgroundSkeleton width="4em" />}
        </DegreeYear>
      </DegreeTitleWrapper>
      <span>
        {!skeleton && editMode ?
          <LightTrashIcon role="button" onClick={() => remove(program.id)}>
            <i className="fa fa-trash fa-md" />
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
  unselectedFulfillments: Fulfillment[]
}
interface RuleTreeInternalNode extends RuleTreeBaseNode {
  type: "INTERNAL_NODE";
  num?: number;
  children: RuleTree[];
}
export type RuleTree = RuleTreeLeaf | RuleTreeInternalNode;
export interface FaultyRuleTree extends RuleTreeLeaf {
  children: RuleTree[];
}

// TODO: factor out activeDegreePlanId so it's not in entire tree
interface RuleProps {
  rule: Rule;
  rulesToFulfillments: { [ruleId: string]: Fulfillment[] };
  rulesToUnselectedFulfillments: { [ruleId: string]: Fulfillment[] };
  activeDegreePlanId: number;
  degree: DegreeD;
}

const computeRuleTree = ({activeDegreePlanId, rule, rulesToFulfillments, rulesToUnselectedFulfillments, degree }: RuleProps): RuleTree => {
  if (rule.q) { // Rule leaf
    const fulfillmentsForRule: Fulfillment[] = rulesToFulfillments[rule.id] || [];
    const unselectedFulfillmentsForRule: Fulfillment[] = rulesToUnselectedFulfillments[rule.id] || [];
    const cus = fulfillmentsForRule.reduce((acc, f) => acc + (f.course?.credits || 1), 0); // default to 1 cu 
    const num = fulfillmentsForRule.length;
    const progress = Math.min(rule.credits ? cus / rule.credits : 1, rule.num ? num / rule.num : 1);
    return { activeDegreePlanId, type: "LEAF", progress, cus, num, rule, fulfillments: fulfillmentsForRule, unselectedFulfillments: unselectedFulfillmentsForRule }
  }
  const children = rule.rules.map((child) => computeRuleTree({ activeDegreePlanId, rule: child, rulesToFulfillments, rulesToUnselectedFulfillments, degree }))
  const progress = children.reduce((acc, { progress }) => progress + acc, 0) / Math.min(children.length, rule.num || Infinity);
  return { num: rule.num || undefined, activeDegreePlanId, type: "INTERNAL_NODE", children, progress, rule } // internal node
}


const Degree = ({ 
  allRuleLeaves, 
  program, 
  rulesToFulfillments, 
  rulesToUnselectedFulfillments, 
  activeDegreeplan, 
  editMode, 
  setModalKey, 
  setModalObject, 
  isLoading 
}: any) => {
  const [collapsed, setCollapsed] = useState(false);

  const headerRef = useRef<HTMLDivElement>(null);
  const [headerHeight, setHeaderHeight] = useState<number>(0);

  useLayoutEffect(() => {
    if (!headerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setHeaderHeight(entry.target.clientHeight);
      }
    });
    resizeObserver.observe(headerRef.current);

    return () => {
      resizeObserver.disconnect();
    }
  }, []);

  if (isLoading) {
    return (
      <div>
        <DegreeHeader
          program={program}
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
        containerRef={headerRef}
        program={program}
        key={program.id}
        remove={() => {
          setModalObject({
            degreeplanId: activeDegreeplan.id,
            degreeId: program.id,
            relation: program.relation,
          });
          setModalKey("degree-remove");
        }}
        setCollapsed={setCollapsed}
        collapsed={collapsed || editMode} // Collapse degree view in edit mode
        editMode={editMode}
        skeleton={false}
      />
      <WhiteSpace $headerHeight={headerHeight} $zIndex={999} />
      {!collapsed && !editMode &&
        <>
          <DegreeBody>
            {program.rules.map((rule: any) => (
              <RuleComponent
                key={rule.id}
                headerHeight={headerHeight}
                zIndex={999}
                {...computeRuleTree({
                  activeDegreePlanId: activeDegreeplan.id,
                  rule,
                  rulesToFulfillments,
                  rulesToUnselectedFulfillments,
                  degree: program,
                })}
              />
            ))}
          </DegreeBody>
        </>
      }
    </div>
  )
}

interface ReqPanelProps {
  setModalKey: (arg0: ModalKey) => void;
  setModalObject: (arg0: DegreePlan | null) => void;
  activeDegreeplan: DegreePlan | null;
  isLoading: boolean;
}
const ReqPanel = ({ setModalKey, setModalObject, activeDegreeplan, isLoading }: ReqPanelProps) => {
  const [editMode, setEditMode] = React.useState(false);
  const [allRuleLeaves, setAllRuleLeaves] = React.useState(false);

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


  const rulesToUnselectedFulfillments = useMemo(() => {
    if (isLoadingFulfillments || !fulfillments) return {};
    const rulesToCourses: { [rule: string]: Fulfillment[] } = {};
    fulfillments.forEach(fulfillment => {
      if (fulfillment.unselected_rules) {
        fulfillment.unselected_rules.forEach(rule => {
          if (!(rule in rulesToCourses)) {
            rulesToCourses[rule] = [];
          }
          rulesToCourses[rule].push(fulfillment);
        });
      }
    });
    return rulesToCourses;
  }, [fulfillments, isLoadingFulfillments])

  return (
    <PanelContainer>
      <PanelHeader>
        <ReqPanelTitle>Requirements</ReqPanelTitle>
        <PanelTopBarIconList>
          <EditButton editMode={editMode} setEditMode={setEditMode} />
        </PanelTopBarIconList>
      </PanelHeader>
      {!activeDegreeplan ? <ReqPanelBody><Degree isLoading={true} /></ReqPanelBody> :
        <>
          {activeDegreeplanDetail &&
            <ReqPanelBody>
              <ReqContent>
                {planPrograms(activeDegreeplanDetail).length == 0 && !editMode && <EmptyPanel />}
                {planPrograms(activeDegreeplanDetail).map(program => (
                  <Degree
                    key={`${program.relation}-${program.id}`}
                    allRuleLeaves={allRuleLeaves}
                    program={program}
                    rulesToFulfillments={rulesToFulfillments}
                    rulesToUnselectedFulfillments={rulesToUnselectedFulfillments}
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
              </ReqContent>
            </ReqPanelBody>
          }
        </>}
    </PanelContainer>
  );
}
export default ReqPanel;
