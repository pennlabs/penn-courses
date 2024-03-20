import React, { useState } from 'react';
import RuleLeaf, { SkeletonRuleLeaf } from './QObject';
import { Course, DnDCourse, Fulfillment, Rule } from '@/types';
import styled from '@emotion/styled';
import { Icon } from '../common/bulma_derived_components';
import { useSWRCrud } from '@/hooks/swrcrud';
import { useDrop } from 'react-dnd';
import { ItemTypes } from '../dnd/constants';
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
import { DegreeYear, RuleTree } from './ReqPanel';

const RuleTitleWrapper = styled.div`
    background-color: var(--primary-color-light);
    position: relative;
    border-radius: var(--req-item-radius);
`

const ProgressBar = styled.div<{$progress: number}>`
    width: ${props => props.$progress * 100}%;
    height: 100%;
    position: absolute;
    background-color: var(--primary-color-dark);
    border-top-left-radius: .3rem;
    border-bottom-left-radius: .3rem;
`

const RuleTitle = styled.div<{$progress: number}>`
  position: relative;
  font-size: 1rem;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  color: #575757;
  padding: 0.25rem .5rem;
  margin: 0.5rem 0;
`

const RuleLeafWrapper = styled.div<{$isDroppable:boolean, $isOver: boolean}>`
  margin: .5rem;
  margin-left: 0;
  display: flex;
  justify-content: space-between;
  gap: .5rem;
  align-items: center;
  box-shadow: ${props => props.$isOver ? '0px 0px 4px 2px var(--selected-color);' : props.$isDroppable ? '0px 0px 4px 2px var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
`

const CusCourses = styled.div`
  font-weight: 500;
  font-size: .9rem;
  white-space: nowrap;
`

const Row = styled.div`
  display: flex;
  gap: .5rem;
`

const Indented = styled.div`
  margin-left: .75rem;
  margin-bottom: 1rem;
`


/**
 * Skeleton of a rule, which excepts children that are skeleton rules. If the skeleton has children, then
 * it is treated as a rule header; otherwise it is treated as a rule leaf.
 */
export const SkeletonRule: React.FC<React.PropsWithChildren> = ({ children }) => (
  <>
    {!children ?
      <RuleLeafWrapper $isDroppable={false} $isOver={false}>
          <SkeletonRuleLeaf />
          <div>
            <CusCourses>
              <Row>
                <DarkBlueBackgroundSkeleton width="1em" />
                <span>/</span>
                <DarkBlueBackgroundSkeleton width="2em" />
              </Row>
            </CusCourses>
          </div>
      </RuleLeafWrapper>
      :
      <RuleTitleWrapper>
        <ProgressBar $progress={0}></ProgressBar>
        <RuleTitle $progress={0}>
          <Row>
            <DarkBlueBackgroundSkeleton width="10em" />
            <DarkBlueBackgroundSkeleton width="7em" />
          </Row>
            <Icon>
              <i className="fas fa-chevron-down" />
            </Icon>
        </RuleTitle>
      </RuleTitleWrapper>
      }
    <div className="ms-3">
      {children}
    </div>
  </>
)

/**
 * Recursive component to represent a rule.
 */
const RuleComponent = (ruleTree : RuleTree) => {
    const { type, activeDegreePlanId, rule, progress } = ruleTree; 
    const satisfied = progress === 1;

    // state for INTERNAL_NODEs
    const [collapsed, setCollapsed] = useState(false);

    // hooks for LEAFs
    const { createOrUpdate } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`,
        { idKey: "full_code",
        createDefaultOptimisticData: { semester: null, rules: [] }
    });

    const [{ isOver, canDrop }, drop] = useDrop<DnDCourse, never, { isOver: boolean, canDrop: boolean }>({
        accept: [ItemTypes.COURSE_IN_PLAN, ItemTypes.COURSE_IN_DOCK], 
        drop: (course: DnDCourse) => {
          createOrUpdate({ rules: [rule.id] }, course.full_code)

        }, // TODO: this doesn't handle fulfillments that already have a rule
        canDrop: () => { return !satisfied && !!rule.q },
        collect: monitor => ({
          isOver: !!monitor.isOver() && !satisfied,
          canDrop: !!monitor.canDrop()
        }),
    }, [createOrUpdate, satisfied]);


    if (type === "LEAF") {
      const { fulfillments, cus, num } = ruleTree;
      return (
        <RuleLeafWrapper $isDroppable={canDrop} $isOver={isOver} ref={drop}>
            <RuleLeaf q_json={rule.q_json} rule={rule} fulfillmentsForRule={fulfillments} satisfied={satisfied} activeDegreePlanId={activeDegreePlanId}/>
            <div>
              {rule.credits && <CusCourses>{cus} / {rule.credits} cus</CusCourses>}
              {" "}
              {rule.num && <CusCourses>{num} / {rule.num}</CusCourses>}
            </div>
        </RuleLeafWrapper>
      )
    }

    // otherwise, type == "INTERNAL_NODE"
    const { children } = ruleTree; 
    return (
      <>
        <RuleTitleWrapper onClick={() => setCollapsed(!collapsed)}>
          <ProgressBar $progress={progress}></ProgressBar>
          <RuleTitle>
            <div>
              {rule.title}
              {" "}
              <DegreeYear>{(progress * 100).toFixed(0)}%</DegreeYear>
            </div>
              {rule.rules.length && 
                  <Icon>
                    <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
                  </Icon>
              }
          </RuleTitle>
        </RuleTitleWrapper>
        {!collapsed &&
          <Indented>
            {children.map((ruleTree) => (
              <div>
                <RuleComponent {...ruleTree} />
              </div>
            ))}
          </Indented>
          }
      </>
    )
}

export default RuleComponent;