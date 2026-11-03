
import { useMemo, useState, useContext, useRef, useLayoutEffect } from 'react';
import RuleComponent, { FulfillmentsLoadedContext, SkeletonRule } from './Rule';
import { Degree as DegreeType, DegreePlan, Fulfillment, Rule, Degree as DegreeD } from '@/types';
import styled from '@emotion/styled';
import { DarkBlueBackgroundSkeleton, PanelBody, PanelContainer, PanelHeader, PanelTopBarIconList } from "../FourYearPlan/PanelCommon";
import { EditButton } from '../FourYearPlan/EditButton';
import useSWR from 'swr';
import { Icon } from '../common/bulma_derived_components';
import React from 'react';
import { ModalKey } from '../FourYearPlan/DegreeModal';
import { LightTrashIcon } from '../common/TrashIcon';
import useStickyState from '@/hooks/stickyState';
import ProgramTabs, { ProgramKind, programPanelId, programTabId } from './ProgramTabs';

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
  background-color: var(--primary-color-ultra-dark);
  color: #FFF;
  padding: 0.75rem 1.25rem;
  border-radius: var(--req-item-radius);
  position: sticky;
  top: 0;
  z-index: 1000;
  overflow: hidden;
  gap: .5rem;
`

const DegreeHeaderFill = styled.div<{ $progress: number }>`
  position: absolute;
  inset: 0 auto 0 0;
  width: ${(props) => props.$progress * 100}%;
  background: rgba(255, 255, 255, 0.16);
  pointer-events: none;
`

const DegreeHeaderAction = styled.span`
  position: relative;
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
  position: relative;
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

const ReqPanelBody = styled(PanelBody)<{ $hasTabs?: boolean }>`
  overflow-y: scroll;
  padding: ${(props) => (props.$hasTabs ? ".85rem 1.5rem 1.5rem" : "1.5rem")};
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
  kind: ProgramKind;
  title: string;
  code: string; // a short label, for when the full title doesn't fit
  year: number;
  rules: Rule[];
}

const programKey = (program: PlanProgram) => `${program.relation}-${program.id}`;

const planPrograms = (detail: DegreePlan): PlanProgram[] => [
  ...(detail.degrees ?? []).map((degree) => ({
    id: degree.id,
    relation: "degrees" as const,
    kind: "degree" as const,
    title: `${degree.degree} in ${degree.major_name}${
      degree.concentration ? ` (${degree.concentration_name})` : ""
    }`,
    code: `${degree.degree} ${degree.major}`,
    year: degree.year,
    rules: degree.rules,
  })),
  ...(detail.majors ?? []).map((major) => ({
    id: major.id,
    relation: "majors" as const,
    kind: "major" as const,
    title: `Major in ${major.name}${
      major.concentration_name ? ` (${major.concentration_name})` : ""
    }`,
    code: major.code,
    year: major.year,
    rules: major.rules,
  })),
  ...(detail.minors ?? []).map((minor) => ({
    id: minor.id,
    relation: "minors" as const,
    kind: "minor" as const,
    title: `Minor in ${minor.name}`,
    code: minor.code,
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
  containerRef?: React.Ref<HTMLDivElement>,
  progress?: number,
}

const DegreeHeader = ({
  program,
  remove,
  setCollapsed,
  collapsed,
  editMode,
  skeleton,
  containerRef,
  progress = 0,
}: DegreeHeaderProps) => {
  const degreeName = !skeleton ? program.title : <DarkBlueBackgroundSkeleton width="10em" />;
  return (
    <DegreeHeaderContainer ref={containerRef} onClick={() => setCollapsed(!collapsed)}>
      <DegreeHeaderFill $progress={editMode ? 0 : progress} />
      <DegreeTitleWrapper>
        <div>
          {degreeName}
        </div>
        <DegreeYear>
          {!skeleton ? program.year : <DarkBlueBackgroundSkeleton width="4em" />}
        </DegreeYear>
      </DegreeTitleWrapper>
      <DegreeHeaderAction>
        {!skeleton && editMode ?
          <LightTrashIcon role="button" onClick={() => remove(program.id)}>
            <i className="fa fa-trash fa-md" />
          </LightTrashIcon>
          :
          <Icon>
            <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
          </Icon>}
      </DegreeHeaderAction>
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
    const progress = Math.min(1, rule.credits ? cus / rule.credits : 1, rule.num ? num / rule.num : 1);
    return { activeDegreePlanId, type: "LEAF", progress, cus, num, rule, fulfillments: fulfillmentsForRule, unselectedFulfillments: unselectedFulfillmentsForRule }
  }
  const children = rule.rules.map((child) => computeRuleTree({ activeDegreePlanId, rule: child, rulesToFulfillments, rulesToUnselectedFulfillments, degree }))
  // A "pick N" rule is only as far along as its N furthest children: extra ones don't count.
  const required = Math.min(children.length, rule.num || Infinity);
  const counted = children.map((child) => child.progress).sort((a, b) => b - a).slice(0, required);
  const progress = required ? counted.reduce((acc, childProgress) => acc + childProgress, 0) / required : 0;
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
  progress,
  showHeader = true, // false when program tabs take the header's place
  stickyOffset = 0, // the height of whatever replaces the header, for sticky rule headers
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
  }, [showHeader, isLoading]); // the header element comes and goes with these

  const ruleOffset = showHeader ? headerHeight : stickyOffset;
  const showRules = !editMode && (!collapsed || !showHeader);

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
          progress={progress}
        />
      )}
      <WhiteSpace $headerHeight={ruleOffset} $zIndex={999} />
      {showRules &&
        <>
          <DegreeBody>
            {program.rules.map((rule: any) => (
              <RuleComponent
                key={rule.id}
                headerHeight={ruleOffset}
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

  const programs = activeDegreeplanDetail ? planPrograms(activeDegreeplanDetail) : [];
  const fulfillmentsLoaded = !isLoadingFulfillments && !!fulfillments;
  // Edit mode manages programs rather than browsing them, so it lists them all.
  const showTabs = programs.length > 1 && !editMode;

  // The average of the program's top-level rules.
  const programProgress = (program: PlanProgram) => {
    if (!program.rules.length) return 0;
    const total = program.rules.reduce((acc, rule) => acc + computeRuleTree({
      activeDegreePlanId: activeDegreeplan?.id as number,
      rule,
      rulesToFulfillments,
      rulesToUnselectedFulfillments,
      degree: program as unknown as DegreeD,
    }).progress, 0);
    return total / program.rules.length;
  };

  const [storedTabKey, setStoredTabKey] = useStickyState<string | null>(
    `PDP-${activeDegreeplan?.id}-requirements-tab`,
    null
  );
  // A remembered program may have since been removed from the plan.
  const activeTabKey = programs.some((program) => programKey(program) === storedTabKey)
    ? storedTabKey as string
    : programs.length ? programKey(programs[0]) : "";

  // Sticky rule headers sit below the tab bar, which grows if a tab's title wraps.
  const [tabBar, setTabBar] = useState<HTMLDivElement | null>(null);
  const [tabBarHeight, setTabBarHeight] = useState(0);
  useLayoutEffect(() => {
    if (!tabBar) return;
    const resizeObserver = new ResizeObserver(() => {
      setTabBarHeight(tabBar.getBoundingClientRect().height);
    });
    resizeObserver.observe(tabBar);
    return () => resizeObserver.disconnect();
  }, [tabBar]);

  return (
    <FulfillmentsLoadedContext.Provider value={fulfillmentsLoaded}>
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
            <ReqPanelBody $hasTabs={showTabs}>
              <ReqContent>
                {programs.length == 0 && !editMode && <EmptyPanel />}
                {showTabs && (
                  <ProgramTabs
                    ref={setTabBar}
                    tabs={programs.map((program) => ({
                      key: programKey(program),
                      kind: program.kind,
                      title: program.title,
                      code: program.code,
                      year: program.year,
                      progress: programProgress(program),
                    }))}
                    activeKey={activeTabKey}
                    onSelect={setStoredTabKey}
                    loaded={fulfillmentsLoaded}
                  />
                )}
                {programs.map((program) => {
                  const key = programKey(program);
                  return (
                    // Other tabs stay mounted, so their collapsed rules survive switching back.
                    <div
                      key={key}
                      id={showTabs ? programPanelId(key) : undefined}
                      role={showTabs ? "tabpanel" : undefined}
                      aria-labelledby={showTabs ? programTabId(key) : undefined}
                      style={showTabs && key !== activeTabKey ? { display: "none" } : undefined}
                    >
                      <Degree
                        allRuleLeaves={allRuleLeaves}
                        program={program}
                        rulesToFulfillments={rulesToFulfillments}
                        rulesToUnselectedFulfillments={rulesToUnselectedFulfillments}
                        activeDegreeplan={activeDegreeplan}
                        editMode={editMode}
                        setModalKey={setModalKey}
                        setModalObject={setModalObject}
                        isLoading={isLoading}
                        progress={programProgress(program)}
                        showHeader={!showTabs}
                        stickyOffset={tabBarHeight}
                      />
                    </div>
                  );
                })}
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
    </FulfillmentsLoadedContext.Provider>
  );
}
export default ReqPanel;
