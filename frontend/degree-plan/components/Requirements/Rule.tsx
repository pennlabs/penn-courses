import React, { createContext, useContext, useEffect, useState, useLayoutEffect, useRef, useCallback } from "react";
import RuleLeaf, { SkeletonRuleLeaf } from "./QObject";
import { DnDCourse, Fulfillment } from "@/types";
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
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import {
  RuleTitleWrapper,
  ProgressBar,
  RuleTitle,
  RuleTitleText,
  RuleLeafWrapper,
  RuleLeafTitle,
  LeafProgress,
  LeafStatus,
  CusCourses,
  Row,
  Indented,
  Column,
  PickNWrapper,
  PickNTitle,
  RuleLeafLabel,
  OverrideTagWrapper,
  OverrideTag,
  OverridePopover,
  OverridePopoverTitle,
  OverrideItem,
  OverrideItemName,
  RemoveOverrideButton,
  OverrideModalOverlay,
  OverrideModalCard,
  OverrideModalTitle,
  OverrideModalBody,
  OverrideModalActions,
  OverrideModalButton,
  OverrideCourseName,
  RuleLeafContainer,
  WaivedTag,
  RemoveWaiverButton,
  WaiveButton,
} from "./Rule.styles";
import { ProgramKind } from "./ProgramTabs";

/** The kind of program the rules below belong to, which colors their accents. */
export const ProgramKindContext = createContext<ProgramKind | null>(null);

/**
 * Whether the fulfillments behind the rule tree have loaded. Every rule reads as 0% until they
 * have, so the first jump to the real values is the page loading rather than the user changing
 * something, and it shouldn't animate.
 */
export const FulfillmentsLoadedContext = createContext(false);

/** Changes to the active plan's waivers, saved in the order they are made (see ReqPanel). */
export const WaiversContext = createContext<{
  setWaived: (ruleId: number, waived: boolean) => void;
  /** Lifts a requirement's waiver by saving a course onto it, which `save` does. */
  liftWaiver: (ruleId: number, save: () => Promise<unknown>) => void;
}>({ setWaived: () => {}, liftWaiver: () => {} });

/** Which of a rule's changes this render should animate. */
const useRuleAnimation = (satisfied: boolean) => {
  const loaded = useContext(FulfillmentsLoadedContext);
  const previous = useRef({ loaded, satisfied });
  const { loaded: wasLoaded, satisfied: wasSatisfied } = previous.current;
  useEffect(() => {
    previous.current = { loaded, satisfied };
  });
  return {
    animateProgress: wasLoaded,
    justSatisfied: wasLoaded && satisfied && !wasSatisfied,
  };
};

/** Whether a dragged course sits in the AP & transfer credit semester. */
const isTransferCredit = (course: DnDCourse) =>
  (course?.semester ?? course?.fulfillment?.semester) === TRANSFER_CREDIT_SEMESTER_KEY;

interface OverrideModalProps {
  fullCode: string;
  ruleTitle: string;
  waived: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const OverrideModal = ({ fullCode, ruleTitle, waived, onConfirm, onCancel }: OverrideModalProps) => (
  <OverrideModalOverlay onClick={onCancel}>
    <OverrideModalCard onClick={(e) => e.stopPropagation()}>
      <OverrideModalTitle>Override Requirement?</OverrideModalTitle>
      <OverrideModalBody>
        <OverrideCourseName>{fullCode.replace("-", " ")}</OverrideCourseName> doesn't
        normally satisfy <OverrideCourseName>{ruleTitle || "this requirement"}</OverrideCourseName>.
        <br /><br />
        Do you want to manually override this and count it anyway?
        {waived && (
          <>
            <br /><br />
            This requirement is currently waived. Counting a course for it removes the waiver.
          </>
        )}
      </OverrideModalBody>
      <OverrideModalActions>
        <OverrideModalButton onClick={onCancel}>Cancel</OverrideModalButton>
        <OverrideModalButton $primary onClick={onConfirm}>Override</OverrideModalButton>
      </OverrideModalActions>
    </OverrideModalCard>
  </OverrideModalOverlay>
);

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
const RuleComponent = (ruleTree: RuleTree & { headerHeight?: number, zIndex?: number, depth?: number }) => {
  const { setCourses, courses } = useContext(ExpandedCoursesPanelContext);
  const programKind = useContext(ProgramKindContext);
  const { type, activeDegreePlanId, rule, progress } = ruleTree;
  const satisfied = progress === 1;
  const { animateProgress, justSatisfied } = useRuleAnimation(satisfied);

  const headerHeight = ruleTree.headerHeight;
  const zIndex = ruleTree.zIndex || -1;
  const depth = ruleTree.depth ?? 0;

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

  // A waiver (e.g. from AP exams) completes a requirement without any course or course units.
  const waived = type === "LEAF" && ruleTree.waived;
  const { setWaived, liftWaiver } = useContext(WaiversContext);
  const toggleWaiver = useCallback(() => setWaived(rule.id, !waived), [setWaived, rule.id, waived]);

  const fulfillmentsKey = `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`;

  const showOnRule = useCallback(
    (fullCode: string, changes: (existing?: Fulfillment) => Partial<Fulfillment>) =>
      mutate<Fulfillment[]>(
        fulfillmentsKey,
        (fulfillments = []) => {
          const existing = fulfillments.find((f) => f.full_code === fullCode);
          const shown = {
            semester: null,
            rules: [],
            unselected_rules: [],
            overrides: [],
            ...existing,
            ...changes(existing),
            full_code: fullCode,
          } as Fulfillment;
          return [...fulfillments.filter((f) => f.full_code !== fullCode), shown];
        },
        { revalidate: false }
      ),
    [mutate, fulfillmentsKey]
  );

  // Counting a course for a waived rule lifts the waiver, so it is saved behind any waiver
  // changes still on their way: the server has to see them in the order they were made.
  const countCourse = useCallback(
    (fullCode: string, data: Partial<Fulfillment>) => {
      if (!waived) {
        createOrUpdate(data, fullCode);
        return;
      }
      showOnRule(fullCode, () => data);
      liftWaiver(rule.id, () => postFetcher(fulfillmentsKey, { ...data, full_code: fullCode }));
    },
    [waived, createOrUpdate, showOnRule, liftWaiver, rule.id, fulfillmentsKey]
  );

  const handleOverrideConfirm = useCallback(() => {
    if (!overrideModal) return;
    const { fullCode, rules = [] } = overrideModal;
    setOverrideModal(null);
    showOnRule(fullCode, (existing) => ({
      rules: Array.from(new Set([...rules, rule.id])),
      overrides: Array.from(new Set([...(existing?.overrides ?? []), rule.id])),
    }));
    // Saved in turn with waiver changes whether or not the rule is waived now, so that waiving
    // it straight afterwards can't reach the server first.
    liftWaiver(rule.id, async () => {
      // The fulfillment has to exist before it can be overridden onto the rule.
      await postFetcher(fulfillmentsKey, { full_code: fullCode, rules });
      await postFetcher(`${fulfillmentsKey}/${fullCode}/override`, { rule_id: rule.id });
    });
  }, [overrideModal, rule.id, fulfillmentsKey, showOnRule, liftWaiver]);

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
          countCourse(course.full_code, {
            rules:
              course.rules !== undefined
                ? [...course.rules, rule.id]
                : [rule.id],
            unselected_rules:
              course.unselected_rules !== undefined
                ? course.unselected_rules
                : [],
          });

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
          countCourse(course.full_code, {
            rules:
              course.rules !== undefined
                ? [...course.rules, rule.id]
                : [rule.id],
          });
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

        if (isTransferCredit(course) && !rule.transfer_credit_allowed) {
          return false;
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
    [countCourse, satisfied, courseMatchesRule, rule.transfer_credit_allowed]
  );

  if (type === "LEAF") {
    const { fulfillments, unselectedFulfillments, cus, num } = ruleTree;
    const overrideFulfillments = fulfillments.filter(
      (f) => f.overrides?.includes(rule.id)
    );
    return (
      <RuleLeafContainer $isDroppable={canDrop} $isOver={isOver} ref={drop} className="rule-leaf">
        {overrideModal && (
          <OverrideModal
            fullCode={overrideModal.fullCode}
            ruleTitle={rule.title}
            waived={waived}
            onConfirm={handleOverrideConfirm}
            onCancel={() => setOverrideModal(null)}
          />
        )}
        <RuleLeafLabel>
          <RuleLeafTitle>{rule.title}</RuleLeafTitle>
          <LeafStatus>
            {!!satisfied && <SatisfiedCheck pop={justSatisfied} />}
            {waived ? (
              <WaivedTag title="Waived, e.g. by an AP exam: complete, with no course units">
                Waived
                <RemoveWaiverButton
                  onClick={toggleWaiver}
                  title="Remove waiver"
                  aria-label={`Remove waiver for ${rule.title}`}
                >
                  <i className="fas fa-times" />
                </RemoveWaiverButton>
              </WaivedTag>
            ) : (
              <>
                {!!rule.credits && (
                  <LeafProgress>
                    {cus} / {rule.credits}
                    <small>{rule.credits > 1 ? "cus" : "cu"}</small>
                  </LeafProgress>
                )}
                {!!rule.num && <LeafProgress>{num}/{rule.num}</LeafProgress>}
              </>
            )}
          </LeafStatus>
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
          {!waived && (
            <WaiveButton
              onClick={toggleWaiver}
              title="Mark as waived, e.g. by an AP exam. It counts as complete but adds no course units."
              aria-label={`Waive ${rule.title}`}
            >
              Waive
            </WaiveButton>
          )}
        </RuleLeafLabel>
        <RuleLeaf
          q_json={rule.q_json}
          rule={rule}
          fulfillmentsForRule={fulfillments}
          unselectedFulfillmentsForRule={unselectedFulfillments}
          satisfied={satisfied}
          activeDegreePlanId={activeDegreePlanId}
        />
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
          {satisfied && <SatisfiedCheck pop={justSatisfied} />}
        </PickNTitle>
        {children.map((ruleTree) => (
          <div key={ruleTree.rule.id}>
            <RuleComponent headerHeight={headerHeight} zIndex={zIndex - 1} depth={depth + 1} {...ruleTree} />
          </div>
        ))}
      </PickNWrapper>
    );
  }

  return (
    <>
      <RuleTitleWrapper $headerHeight={headerHeight} $zIndex={zIndex} $depth={depth} $kind={programKind} onClick={() => setCollapsed(!collapsed)} ref={myHeaderRef}>
        <ProgressBar $progress={progress} $animate={animateProgress} $depth={depth}></ProgressBar>
        <RuleTitle $depth={depth}>
          <RuleTitleText $stacked={depth === 0}>
            <span>{rule.title}</span> <DegreeYear>{(progress * 100).toFixed(0)}%</DegreeYear>
          </RuleTitleText>
          {rule.rules.length > 0 && (
            <Icon>
              <i className={`fas fa-chevron-${collapsed ? "right" : "up"}`}></i>
            </Icon>
          )}
        </RuleTitle>
      </RuleTitleWrapper>
      <WhiteSpace $headerHeight={myHeight + (headerHeight ||0) + HEADER_DEFAULT_BUFFER} $zIndex={500} />
      {!collapsed && (
        <Indented $depth={depth}>
          <Column>
            {children.map((ruleTree) => (
              <div key={ruleTree.rule.id}>
                <RuleComponent headerHeight={myHeight + (headerHeight || 0) + HEADER_DEFAULT_BUFFER} zIndex={zIndex - 1} depth={depth + 1} {...ruleTree} />
              </div>
            ))}
          </Column>
        </Indented>
      )}
    </>
  );
};

export default RuleComponent;
