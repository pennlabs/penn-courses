import React, { useContext, useEffect, useState, useLayoutEffect, useRef } from "react";
import RuleLeaf, { SkeletonRuleLeaf } from "./QObject";
import { DnDCourse, Fulfillment } from "@/types";
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import { useSWRCrud } from "@/hooks/swrcrud";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
import { DegreeYear, RuleTree, WhiteSpace, HEADER_DEFAULT_BUFFER } from "./ReqPanel";
import SatisfiedCheck from "../FourYearPlan/SatisfiedCheck";
import { ExpandedCoursesPanelContext } from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";
import { parseQJson } from "./ruleUtils";

const RuleTitleWrapper = styled.div<{ $headerHeight?: number, $zIndex?: number }>`
  background-color: var(--primary-color);
  position: sticky;
  border-radius: var(--req-item-radius);
  top: ${(props) => (props.$headerHeight || 0) + HEADER_DEFAULT_BUFFER}px;
  z-index: ${(props) => props.$zIndex || 995};
`;

const ProgressBar = styled.div<{ $progress: number }>`
  width: ${(props) => props.$progress * 100}%;
  height: 100%;
  position: absolute;
  background-color: var(--primary-color-dark);
  border-top-left-radius: 0.3rem;
  border-bottom-left-radius: 0.3rem;
`;

const RuleTitle = styled.div`
  position: relative;
  font-size: 1rem;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  color: #575757;
  padding: 0.5rem 1.25rem;
  margin-bottom: 0.5rem;
`;

const RuleLeafWrapper = styled.div<{ $isDroppable: boolean; $isOver: boolean }>`
  padding: 0.5rem 0.5rem 0.5rem 0rem;
  margin-left: 0;
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
  box-shadow: ${(props) =>
    props.$isOver && props.$isDroppable
      ? "0px 0px 4px 2px var(--selected-color);"
      : props.$isDroppable
      ? "0px 0px 4px 2px var(--primary-color-dark);"
      : "rgba(0, 0, 0, 0.05);"};
`;

const CusCourses = styled.div`
  font-weight: 500;
  font-size: 0.9rem;
  white-space: nowrap;

  sup {
    margin-right: 0.2em;
  }

  sub {
    margin-left: 0.2em;
  }
`;

const Row = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const Indented = styled.div`
  margin-left: 0.75rem;
  margin-bottom: 0.5rem;
`;

const Column = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0rem;
`;

const PickNWrapper = styled.div`
  background-color: var(--primary-color-extra-light);
  padding: 0.5rem;
  padding-bottom: 0.25rem;
  border-radius: 0.5rem;
`;

const PickNTitle = styled.div`
  display: flex;
  font-weight: 500;
  font-size: 1.05rem;
  margin-bottom: 1rem;
  margin-left: 0.25rem;
  justify-content: space-between;
`;

const RuleLeafLabel = styled.div`
  font-size: 0.9rem;
`;

const RuleLeafContainer = styled(Column)`
  margin-top: 0.25rem;
`;

/**
 * Skeleton of a rule, which excepts children that are skeleton rules. If the skeleton has children, then
 * it is treated as a rule header; otherwise it is treated as a rule leaf.
 */
export const SkeletonRule: React.FC<React.PropsWithChildren> = ({
  children,
}) => (
  <>
    {!children ? (
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
    ) : (
      <RuleTitleWrapper>
        <ProgressBar $progress={0}></ProgressBar>
        <RuleTitle>
          <Row>
            <DarkBlueBackgroundSkeleton width="10em" />
            <DarkBlueBackgroundSkeleton width="7em" />
          </Row>
          <Icon>
            <i className="fas fa-chevron-down" />
          </Icon>
        </RuleTitle>
      </RuleTitleWrapper>
    )}
    <div className="ms-3">{children}</div>
  </>
);

/**
 * Recursive component to represent a rule.
 */
const RuleComponent = (ruleTree: RuleTree & { headerHeight?: number, zIndex?: number }) => {
  const { setCourses, courses } = useContext(ExpandedCoursesPanelContext);
  const { type, activeDegreePlanId, rule, progress } = ruleTree;
  const satisfied = progress === 1;

  const headerHeight = ruleTree.headerHeight;
  const zIndex = ruleTree.zIndex || 5;

  const myHeaderRef = useRef<HTMLDivElement>(null);
  const [myHeight, setMyHeight] = useState(0);

  useLayoutEffect(() => {
    if (!myHeaderRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target instanceof HTMLElement) {
          setMyHeight(entry.target.clientHeight);
        }
      }
    });
    resizeObserver.observe(myHeaderRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, [rule.id]);

  // state for INTERNAL_NODEs
  const [collapsed, setCollapsed] = useState(false);

  // hooks for LEAFs
  const { createOrUpdate } = useSWRCrud<Fulfillment>(
    `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`,
    {
      idKey: "full_code",
      createDefaultOptimisticData: { semester: null, rules: [] },
    }
  );

  // Handle 

  const [{ isOver, canDrop }, drop] = useDrop<
    DnDCourse,
    never,
    { isOver: boolean; canDrop: boolean }
  >(
    {
      accept: [
        ItemTypes.COURSE_IN_PLAN,
        ItemTypes.COURSE_IN_DOCK,
        ItemTypes.COURSE_IN_EXPAND,
        ItemTypes.COURSE_IN_SEARCH,
      ],
      drop: (course: DnDCourse, monitor) => {
        if (monitor.getItemType() === ItemTypes.COURSE_IN_EXPAND) {
          course.unselected_rules?.splice(
            course.unselected_rules?.indexOf(rule.id),
            1
          );
          createOrUpdate(
            {
              rules:
                course.rules !== undefined
                  ? [...course.rules, rule.id]
                  : [rule.id],
              unselected_rules:
                course.unselected_rules !== undefined
                  ? course.unselected_rules
                  : [],
            },
            course.full_code
          );

          let new_courses = courses?.filter((fulfillment) => {
            if (fulfillment.full_code !== course.full_code) {
              return fulfillment;
            }
          });

          setCourses(new_courses);
        } else {
          createOrUpdate(
            {
              rules:
                course.rules !== undefined
                  ? [...course.rules, rule.id]
                  : [rule.id],
            },
            course.full_code
          );
        }
        return undefined;
      }, // TODO: this doesn't handle fulfillments that already have a rule
      canDrop: (course: DnDCourse, monitor) => {
        if (
          monitor.getItemType() === ItemTypes.COURSE_IN_EXPAND ||
          monitor.getItemType() === ItemTypes.COURSE_IN_SEARCH
        ) {
          return rule.id === course.rule_id;
        }

        // Right now, if you drag from dock to reqPanel there's no semester, so we just have an X button on the course.
        // Looks buggy, so I'm just disabling that and only allowing users to drag to semester panel.
        if (monitor.getItemType() === ItemTypes.COURSE_IN_DOCK) {
          const formattedCourse = {
            course: {
              attribute_codes: [],
            },
            full_code: "TMP-0000",
          };

          return parseQJson(rule.q_json, formattedCourse);
        }

        if (course?.course?.attribute_codes) {
          return parseQJson(rule.q_json, course);
        } else {
          return true;
        }
      },
      collect: (monitor) => {
        if (monitor.getItemType() === ItemTypes.COURSE_IN_EXPAND) {
          return {
            isOver: !!monitor.isOver() && rule.id === monitor.getItem().rule_id,
            canDrop: !!monitor.canDrop(),
          };
        }
        return {
          isOver: !!monitor.isOver(),
          canDrop: !!monitor.canDrop(),
        };
      },
    },
    [createOrUpdate, satisfied]
  );

  if (type === "LEAF") {
    const { fulfillments, unselectedFulfillments, cus, num } = ruleTree;
    return (
      <RuleLeafContainer>
        <RuleLeafLabel>{rule.title}</RuleLeafLabel>
        <RuleLeafWrapper $isDroppable={canDrop} $isOver={isOver} ref={drop}>
          <RuleLeaf
            q_json={rule.q_json}
            rule={rule}
            fulfillmentsForRule={fulfillments}
            unselectedFulfillmentsForRule={unselectedFulfillments}
            satisfied={satisfied}
            activeDegreePlanId={activeDegreePlanId}
          />
          <Row>
            {!!satisfied && <SatisfiedCheck />}
            <Column>
              {rule.credits && (
                <CusCourses>
                  <sup>{cus}</sup>/<sub>{rule.credits}</sub>
                  <div>{rule.credits > 1 ? "cus" : "cu"}</div>
                </CusCourses>
              )}{" "}
              {rule.num && (
                <CusCourses>
                  <sup>{num}</sup>/<sub>{rule.num}</sub>
                </CusCourses>
              )}
            </Column>
          </Row>
        </RuleLeafWrapper>
      </RuleLeafContainer>
    );
  }

  // otherwise, type == "INTERNAL_NODE"
  const { children, num } = ruleTree;

  if (num && children.length > num) {
    return (
      <PickNWrapper>
        <PickNTitle>
          <div>Pick {num}:</div>
          {satisfied && <SatisfiedCheck />}
        </PickNTitle>
        {children.map((ruleTree) => (
          <div>
            <RuleComponent {...ruleTree} />
          </div>
        ))}
      </PickNWrapper>
    );
  }

  return (
    <>
      <RuleTitleWrapper $headerHeight={headerHeight} $zIndex={zIndex} onClick={() => setCollapsed(!collapsed)} ref={myHeaderRef}>
        <ProgressBar $progress={progress}></ProgressBar>
        <RuleTitle>
          <div>
            {rule.title} <DegreeYear>{(progress * 100).toFixed(0)}%</DegreeYear>
          </div>
          {rule.rules.length && (
            <Icon>
              <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
            </Icon>
          )}
        </RuleTitle>
      </RuleTitleWrapper>
      <WhiteSpace $headerHeight={myHeight + (headerHeight ||0) + HEADER_DEFAULT_BUFFER} />
      {!collapsed && (
        <Indented>
          <Column>
            {children.map((ruleTree) => (
              <div>
                <RuleComponent headerHeight={myHeight + (headerHeight || 0) + HEADER_DEFAULT_BUFFER} zIndex={zIndex - 1} {...ruleTree} />
              </div>
            ))}
          </Column>
        </Indented>
      )}
    </>
  );
};

export default RuleComponent;
