import React, { useContext, useEffect, useState, useLayoutEffect, useRef, useCallback } from "react";
import RuleLeaf, { SkeletonRuleLeaf } from "./QObject";
import { DnDCourse, Fulfillment } from "@/types";
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import { baseFetcher, postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
import { DegreeYear, RuleTree, FaultyRuleTree, WhiteSpace, HEADER_DEFAULT_BUFFER } from "./ReqPanel";
import SatisfiedCheck from "../FourYearPlan/SatisfiedCheck";
import { ExpandedCoursesPanelContext } from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";
import { parseQJson } from "./ruleUtils";
import { useSWRConfig } from "swr";

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
  display: flex;
  align-items: center;
  gap: 0.4rem;
`;

const OverrideTagWrapper = styled.div`
  position: relative;
  display: inline-flex;
`;

const OverrideTag = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #b8860b;
  background: #fff7d6;
  border: 1px solid #e8d88c;
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  cursor: pointer;

  &:hover {
    background: #fff0b3;
  }
`;

const OverridePopover = styled.div`
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 0.6rem 0.75rem;
  z-index: 1000;
  min-width: 200px;
  font-size: 0.8rem;
`;

const OverridePopoverTitle = styled.div`
  font-weight: 600;
  font-size: 0.7rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 0.4rem;
`;

const OverrideItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;

  &:not(:last-child) {
    border-bottom: 1px solid #f0f0f0;
  }
`;

const OverrideItemName = styled.span`
  color: #333;
  font-weight: 500;
`;

const RemoveOverrideButton = styled.button`
  background: none;
  border: none;
  color: #c0392b;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0.15rem 0.35rem;
  border-radius: 4px;

  &:hover {
    background: #fdecea;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Override modal styles
const OverrideModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(112, 112, 112, 0.75);
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const OverrideModalCard = styled.div`
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
`;

const OverrideModalTitle = styled.div`
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
  color: var(--modal-title-color, #333);
`;

const OverrideModalBody = styled.div`
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 1.25rem;
  line-height: 1.5;
`;

const OverrideModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
`;

const OverrideModalButton = styled.button<{ $primary?: boolean }>`
  padding: 0.45rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid ${(props) => (props.$primary ? "#7876f3" : "#d6d6d6")};
  background: ${(props) => (props.$primary ? "#7876f3" : "white")};
  color: ${(props) => (props.$primary ? "white" : "#333")};

  &:hover {
    background: ${(props) => (props.$primary ? "#6e76cd" : "#f5f5f5")};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const OverrideCourseName = styled.strong`
  color: #333;
`;

interface OverrideModalProps {
  fullCode: string;
  ruleTitle: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

const OverrideModal = ({ fullCode, ruleTitle, onConfirm, onCancel, isLoading }: OverrideModalProps) => (
  <OverrideModalOverlay onClick={onCancel}>
    <OverrideModalCard onClick={(e) => e.stopPropagation()}>
      <OverrideModalTitle>Override Requirement?</OverrideModalTitle>
      <OverrideModalBody>
        <OverrideCourseName>{fullCode.replace("-", " ")}</OverrideCourseName> doesn't
        normally satisfy <OverrideCourseName>{ruleTitle || "this requirement"}</OverrideCourseName>.
        <br /><br />
        Do you want to manually override this and count it anyway?
      </OverrideModalBody>
      <OverrideModalActions>
        <OverrideModalButton onClick={onCancel} disabled={isLoading}>Cancel</OverrideModalButton>
        <OverrideModalButton $primary onClick={onConfirm} disabled={isLoading}>
          {isLoading ? "Overriding..." : "Override"}
        </OverrideModalButton>
      </OverrideModalActions>
    </OverrideModalCard>
  </OverrideModalOverlay>
);

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
  const zIndex = ruleTree.zIndex || -1;

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
  const { mutate } = useSWRConfig();

  // Override modal state (for adding overrides via drag)
  const [overrideModal, setOverrideModal] = useState<{ fullCode: string; rules?: number[] } | null>(null);
  const [overrideLoading, setOverrideLoading] = useState(false);

  // Override popover state (for viewing/removing overrides)
  const [overridePopoverOpen, setOverridePopoverOpen] = useState(false);
  const [removingOverride, setRemovingOverride] = useState<string | null>(null);
  const overridePopoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!overridePopoverOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (overridePopoverRef.current && !overridePopoverRef.current.contains(e.target as Node)) {
        setOverridePopoverOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [overridePopoverOpen]);

  const deleteFetcher = baseFetcher({ method: "DELETE" }, false);

  const handleRemoveOverride = useCallback(async (fullCode: string) => {
    setRemovingOverride(fullCode);
    try {
      await deleteFetcher(
        `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments/${fullCode}/override/${rule.id}`
      );
      await mutate(`/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`);
    } finally {
      setRemovingOverride(null);
    }
  }, [activeDegreePlanId, rule.id, mutate, deleteFetcher]);

  const handleOverrideConfirm = useCallback(async () => {
    if (!overrideModal) return;
    setOverrideLoading(true);
    try {
      // Create the fulfillment first so it exists before adding the override
      await createOrUpdate(
        {
          rules: overrideModal.rules !== undefined
            ? overrideModal.rules
            : [],
        },
        overrideModal.fullCode
      );
      // Then add the override (which also adds the rule to the fulfillment)
      await postFetcher(
        `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments/${overrideModal.fullCode}/override`,
        { rule_id: rule.id }
      );
      await mutate(`/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`);
    } finally {
      setOverrideLoading(false);
      setOverrideModal(null);
    }
  }, [overrideModal, rule.id, activeDegreePlanId, createOrUpdate, mutate]);

  /** Returns true if the course natively satisfies this rule (no override needed) */
  const courseMatchesRule = useCallback((course: DnDCourse) => {
    if (course?.course?.attribute_codes) {
      return parseQJson(rule.q_json, course);
    }
    // If we can't check (no attribute_codes), assume it matches
    return true;
  }, [rule.q_json]);

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
        } else if (!courseMatchesRule(course)) {
          // Course doesn't match rule — show override confirmation modal
          setOverrideModal({ fullCode: course.full_code, rules: course.rules });
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

        // Always allow dropping from the plan — if the course doesn't match,
        // the drop handler will prompt for an override instead.
        return true;
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
    [createOrUpdate, satisfied, courseMatchesRule]
  );

  if (type === "LEAF") {
    const { fulfillments, unselectedFulfillments, cus, num } = ruleTree;
    const overrideFulfillments = fulfillments.filter(
      (f) => f.overrides?.includes(rule.id)
    );
    return (
      <RuleLeafContainer>
        {overrideModal && (
          <OverrideModal
            fullCode={overrideModal.fullCode}
            ruleTitle={rule.title}
            onConfirm={handleOverrideConfirm}
            onCancel={() => setOverrideModal(null)}
            isLoading={overrideLoading}
          />
        )}
        <RuleLeafLabel>
          {rule.title}
          {overrideFulfillments.length > 0 && (
            <OverrideTagWrapper ref={overridePopoverRef}>
              <OverrideTag onClick={() => setOverridePopoverOpen(!overridePopoverOpen)}>
                <i className="fas fa-star" />
                {overrideFulfillments.length} {overrideFulfillments.length === 1 ? "override" : "overrides"}
              </OverrideTag>
              {overridePopoverOpen && (
                <OverridePopover>
                  <OverridePopoverTitle>Manual Overrides</OverridePopoverTitle>
                  {overrideFulfillments.map((f) => (
                    <OverrideItem key={f.full_code}>
                      <OverrideItemName>{f.full_code.replace("-", " ")}</OverrideItemName>
                      <RemoveOverrideButton
                        onClick={() => handleRemoveOverride(f.full_code)}
                        disabled={removingOverride === f.full_code}
                      >
                        {removingOverride === f.full_code ? "..." : <i className="fas fa-times" />}
                      </RemoveOverrideButton>
                    </OverrideItem>
                  ))}
                </OverridePopover>
              )}
            </OverrideTagWrapper>
          )}
        </RuleLeafLabel>
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
    /** 
    * This was a hack to fix the data format from physics 
    * requirements for engineering degree
    */
    for (let i = 0; i < children.length; i++) {
      if (children[i].rule.rules.length == 0) {
        continue;
      }

      if ((children[i] as FaultyRuleTree).children) {
        children[i] = (children[i] as FaultyRuleTree).children[0];
      }
    }

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
      <WhiteSpace $headerHeight={myHeight + (headerHeight ||0) + HEADER_DEFAULT_BUFFER} $zIndex={500} />
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
