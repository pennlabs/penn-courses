
import { useMemo, useState, useContext, useRef, useLayoutEffect } from 'react';
import RuleComponent, { FulfillmentsLoadedContext, ProgramKindContext, SkeletonRule } from './Rule';
import { Degree as DegreeType, DegreePlan, Fulfillment, Rule, Degree as DegreeD } from '@/types';
import styled from '@emotion/styled';
import { DarkBlueBackgroundSkeleton, PanelBody, PanelContainer, PanelHeader, PanelTopBarIconList } from "../FourYearPlan/PanelCommon";
import { EditButton } from '../FourYearPlan/EditButton';
import useSWR from 'swr';
import { Icon } from '../common/bulma_derived_components';
import React from 'react';
import useStickyState from '@/hooks/stickyState';
import ProgramTabs, { programPanelId, programTabId } from './ProgramTabs';
import { PlanProgram, planPrograms } from '@/utils/programs';

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

const EmptyPanelButton = styled.button`
  margin-top: 1rem;
  padding: .6rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--primary-color-light);
  color: var(--primary-color-xxx-dark);
  font: inherit;
  font-weight: 600;

  &:hover {
    background: var(--primary-color-dark);
    color: var(--primary-color-ultra-dark);
  }
`;

const EmptyPanel = ({ onAdd }: { onAdd: () => void }) => {
  return (
    <EmptyPanelContainer>
      <EmptyPanelImage src="/images/empty-state-cal.svg" />
      There's nothing here so far... add a degree to get started!
      <EmptyPanelButton type="button" onClick={onAdd}>Add a degree</EmptyPanelButton>
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

const programKey = (program: PlanProgram) => `${program.relation}-${program.id}`;

interface DegreeHeaderProps {
  program: PlanProgram,
  setCollapsed: (status: boolean) => void,
  collapsed: boolean,
  skeleton?: boolean,
  containerRef?: React.Ref<HTMLDivElement>,
  progress?: number,
}

const DegreeHeader = ({
  program,
  setCollapsed,
  collapsed,
  skeleton,
  containerRef,
  progress = 0,
}: DegreeHeaderProps) => {
  const degreeName = !skeleton ? program.title : <DarkBlueBackgroundSkeleton width="10em" />;
  return (
    <DegreeHeaderContainer ref={containerRef} onClick={() => setCollapsed(!collapsed)}>
      <DegreeHeaderFill $progress={progress} />
      <DegreeTitleWrapper>
        <div>
          {degreeName}
        </div>
        <DegreeYear>
          {!skeleton ? program.year : <DarkBlueBackgroundSkeleton width="4em" />}
        </DegreeYear>
      </DegreeTitleWrapper>
      <DegreeHeaderAction>
        <Icon>
          <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
        </Icon>
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
  waived: boolean; // the student is waived from this requirement, e.g. by an AP exam
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
  waivedRules: Set<number>; // the plan's waived requirements, which are always leaves
}

const computeRuleTree = ({activeDegreePlanId, rule, rulesToFulfillments, rulesToUnselectedFulfillments, degree, waivedRules }: RuleProps): RuleTree => {
  if (rule.q) { // Rule leaf
    // A waived requirement is complete without any course.
    const waived = waivedRules.has(rule.id);
    const fulfillmentsForRule: Fulfillment[] = rulesToFulfillments[rule.id] || [];
    const unselectedFulfillmentsForRule: Fulfillment[] = rulesToUnselectedFulfillments[rule.id] || [];
    const cus = fulfillmentsForRule.reduce((acc, f) => acc + (f.course?.credits || 1), 0); // default to 1 cu 
    const num = fulfillmentsForRule.length;
    const progress = waived ? 1 : Math.min(1, rule.credits ? cus / rule.credits : 1, rule.num ? num / rule.num : 1);
    return { activeDegreePlanId, type: "LEAF", progress, waived, cus, num, rule, fulfillments: fulfillmentsForRule, unselectedFulfillments: unselectedFulfillmentsForRule }
  }
  const children = rule.rules.map((child) => computeRuleTree({ activeDegreePlanId, rule: child, rulesToFulfillments, rulesToUnselectedFulfillments, degree, waivedRules }))
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
  waivedRules,
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
  const showRules = !collapsed || !showHeader;

  if (isLoading) {
    return (
      <div>
        <DegreeHeader
          program={program}
          setCollapsed={setCollapsed}
          skeleton
          collapsed={collapsed}
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
          setCollapsed={setCollapsed}
          collapsed={collapsed}
          skeleton={false}
          progress={progress}
        />
      )}
      <WhiteSpace $headerHeight={ruleOffset} $zIndex={999} />
      {showRules &&
        <ProgramKindContext.Provider value={program.kind}>
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
                  waivedRules,
                })}
              />
            ))}
          </DegreeBody>
        </ProgramKindContext.Provider>
      }
    </div>
  )
}

interface ReqPanelProps {
  activeDegreeplan: DegreePlan | null;
  isLoading: boolean;
  onEditPrograms: () => void;
}
const ReqPanel = ({ activeDegreeplan, isLoading, onEditPrograms }: ReqPanelProps) => {
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

  const waivedRules = useMemo(
    () => new Set(activeDegreeplanDetail?.waived_rules ?? []),
    [activeDegreeplanDetail]
  );

  const programs = activeDegreeplanDetail ? planPrograms(activeDegreeplanDetail) : [];
  const fulfillmentsLoaded = !isLoadingFulfillments && !!fulfillments;
  const showTabs = programs.length > 1;

  // The average of the program's top-level rules.
  const programProgress = (program: PlanProgram) => {
    if (!program.rules.length) return 0;
    const total = program.rules.reduce((acc, rule) => acc + computeRuleTree({
      activeDegreePlanId: activeDegreeplan?.id as number,
      rule,
      rulesToFulfillments,
      rulesToUnselectedFulfillments,
      degree: program as unknown as DegreeD,
      waivedRules,
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
          <EditButton editMode={false} setEditMode={onEditPrograms} />
        </PanelTopBarIconList>
      </PanelHeader>
      {!activeDegreeplan ? <ReqPanelBody><Degree isLoading={true} /></ReqPanelBody> :
        <>
          {activeDegreeplanDetail &&
            <ReqPanelBody $hasTabs={showTabs}>
              <ReqContent>
                {programs.length == 0 && <EmptyPanel onAdd={onEditPrograms} />}
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
                        waivedRules={waivedRules}
                        isLoading={isLoading}
                        progress={programProgress(program)}
                        showHeader={!showTabs}
                        stickyOffset={tabBarHeight}
                      />
                    </div>
                  );
                })}
              </ReqContent>
            </ReqPanelBody>
          }
        </>}
    </PanelContainer>
    </FulfillmentsLoadedContext.Provider>
  );
}
export default ReqPanel;
