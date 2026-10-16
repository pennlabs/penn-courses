
import { useMemo, useState, useContext, useRef, useLayoutEffect, useEffect } from 'react';
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
import PlanSummaryBar from './PlanSummaryBar';
import { centerInRequirements, containsRule, subscribeRuleNav } from '@/hooks/requirementNav';
import { PanelOption, PanelOptionsContext } from './QObject';
import { programColor } from '../FourYearPlan/programColor';

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
  gap: 8px;
  font-size: var(--type-body);
  font-weight: 700;
  line-height: 1.25;
  background-color: var(--primary-color-xx-dark);
  color: #FFF;
  padding: 6px 10px;
  border-radius: 6px;
  position: sticky;
  top: 0;
  z-index: 1000;
`

const ReqPanelTitle = styled.div`
  font-size: var(--type-title);
  font-weight: 700; 
`

const DegreeBody = styled.div`
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
`

const TabRow = styled.div`
  display: flex;
  width: 100%;
  position: sticky;
  top: 0;
  z-index: 1001;
  background: #fff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
`;

const Tab = styled.button<{ $active: boolean }>`
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
  margin: 0;
  padding: 8px 10px;
  border: none;
  border-bottom: 3px solid ${(props) => (props.$active ? "var(--primary-color-xx-dark)" : "transparent")};
  background: ${(props) => (props.$active ? "rgba(98, 116, 241, 0.12)" : "transparent")};
  color: inherit;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;

  span {
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
`;

export const DegreeYear = styled.span`
  margin-left: .25rem;
  font-size: var(--type-body);
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

const ReqPanelShell = styled(PanelContainer)`
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
`

const ReqPanelBody = styled(PanelBody)`
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
  overflow-y: scroll;
  padding: 0.55rem 0.65rem;
  gap: 0;
`

// pr, mr for scroll bar
const ReqContent = styled.div`
  min-width: 0;
  max-width: 100%;
  padding: 0;
  padding-right: 12px;
  margin-right: -12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-x: hidden;
  overflow-y: scroll;
`

export const HEADER_DEFAULT_BUFFER = 2;
export const WhiteSpace = styled.div<{ $headerHeight: number, $zIndex: number }>`
  height: ${HEADER_DEFAULT_BUFFER}px;
  background-color: white;
  z-index: ${(props) => props.$zIndex || 500};
  position: sticky;
  top: ${(props) => props.$headerHeight}px;
`

export interface PlanProgram {
  id: number | null;
  key: string;
  relation: "degrees" | "majors" | "minors" | "college" | "degree-major";
  role: string;
  title: string;
  year: number | null;
  removable: boolean;
  rules: Rule[];
}

const ROLE_LABELS: { [role: string]: string } = {
  primary_degree: "Primary degree",
  second_degree: "Second degree",
  second_major: "Second major",
  major: "Major",
  minor: "Minor",
  college: "College",
};

const planPrograms = (detail: DegreePlan): PlanProgram[] => {
  if (detail.components?.length) {
    return detail.components.map((component) => ({
      id: component.id,
      key: component.key,
      relation: component.relation,
      role: component.role,
      title: component.title,
      year: component.year,
      removable: component.removable,
      rules: component.rules,
    }));
  }
  return [
    ...(detail.degrees ?? []).map((degree) => ({
      id: degree.id,
      key: `degree:${degree.id}`,
      relation: "degrees" as const,
      role: "primary_degree",
      title: `${degree.degree} in ${degree.major_name}${
        degree.concentration ? ` (${degree.concentration_name})` : ""
      }`,
      year: degree.year,
      removable: true,
      rules: degree.rules,
    })),
    ...(detail.majors ?? []).map((major) => ({
      id: major.id,
      key: `major:${major.id}`,
      relation: "majors" as const,
      role: "second_major",
      title: `Major in ${major.name}${
        major.concentration_name ? ` (${major.concentration_name})` : ""
      }`,
      year: major.year,
      removable: true,
      rules: major.rules,
    })),
    ...(detail.minors ?? []).map((minor) => ({
      id: minor.id,
      key: `minor:${minor.id}`,
      relation: "minors" as const,
      role: "minor",
      title: `Minor in ${minor.name}`,
      year: minor.year,
      removable: true,
      rules: minor.rules,
    })),
  ];
};

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
          {!skeleton && ROLE_LABELS[program.role] && (
            <span style={{ marginLeft: "0.6em", fontSize: "var(--type-body)", opacity: 0.8 }}>
              {ROLE_LABELS[program.role]}
            </span>
          )}
        </div>
        <DegreeYear>
          {!skeleton && program.year ? program.year : skeleton ? <DarkBlueBackgroundSkeleton width="4em" /> : null}
        </DegreeYear>
      </DegreeTitleWrapper>
      <span>
        {!skeleton && editMode && program.removable ?
          <LightTrashIcon role="button" onClick={() => program.id != null && remove(program.id)}>
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
  isLoading,
  showHeader = true,
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
      {showHeader && (
        <>
          <DegreeHeader
            containerRef={headerRef}
            program={program}
            key={program.id}
            remove={() => {
              if (!program.removable || program.id == null) return;
              // A College double major's major block is removed by removing that degree.
              const relation = program.relation === "degree-major" ? "degrees" : program.relation;
              setModalObject({
                degreeplanId: activeDegreeplan.id,
                degreeId: program.id,
                relation,
              });
              setModalKey("degree-remove");
            }}
            setCollapsed={setCollapsed}
            collapsed={collapsed || editMode} // Collapse degree view in edit mode
            editMode={editMode}
            skeleton={false}
          />
          <WhiteSpace $headerHeight={headerHeight} $zIndex={999} />
        </>
      )}
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
  const [activeProgramKey, setActiveProgramKey] = React.useState<string | null>(null);
  const [focusRule, setFocusRule] = React.useState<{ id: number; nonce: number } | null>(null);

  const { data: activeDegreeplanDetail = null, isLoading: isLoadingDegrees } = useSWR<DegreePlan>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}` : null);
  const { data: panelOptions = {} } = useSWR<Record<string, PanelOption>>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}/panel-options` : null);
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

  const programs = activeDegreeplanDetail ? planPrograms(activeDegreeplanDetail) : [];

  useEffect(() => subscribeRuleNav((ruleId) => {
    const program = programs.find((item) => containsRule(item.rules, ruleId));
    if (program && programs.length > 1) setActiveProgramKey(program.key);
    setFocusRule({ id: ruleId, nonce: Date.now() });
  }), [programs]);

  useEffect(() => {
    if (focusRule == null) return undefined;
    const timer = window.setTimeout(() => centerInRequirements(focusRule.id), 60);
    return () => window.clearTimeout(timer);
  }, [focusRule, activeProgramKey]);

  return (
    <PanelOptionsContext.Provider value={panelOptions}>
    <ReqPanelShell>
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
              <ReqContent id="requirements-scroll">
                {programs.length == 0 && !editMode && <EmptyPanel />}
                <PlanSummaryBar degreePlanId={activeDegreeplan.id} />
                {programs.length > 1 && (
                  <TabRow>
                    {programs.map((program, index) => (
                      <Tab
                        key={program.key}
                        type="button"
                        $active={program.key === (activeProgramKey || programs[0].key)}
                        onClick={() => setActiveProgramKey(program.key)}
                        style={{ boxShadow: `inset 4px 0 0 ${programColor(index)}` }}
                      >
                        <span>{program.title}</span>
                        {program.year && <span style={{ fontWeight: 500, opacity: 0.75 }}>{program.year}</span>}
                      </Tab>
                    ))}
                  </TabRow>
                )}
                {programs
                  .filter((program) => programs.length < 2 || program.key === (activeProgramKey || programs[0].key))
                  .map(program => (
                  <Degree
                    key={program.key}
                    allRuleLeaves={allRuleLeaves}
                    program={program}
                    rulesToFulfillments={rulesToFulfillments}
                    rulesToUnselectedFulfillments={rulesToUnselectedFulfillments}
                    activeDegreeplan={activeDegreeplan}
                    editMode={editMode}
                    setModalKey={setModalKey}
                    setModalObject={setModalObject}
                    isLoading={isLoading}
                    showHeader={programs.length < 2 || editMode}
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
    </ReqPanelShell>
    </PanelOptionsContext.Provider>
  );
}
export default ReqPanel;
