import React, { useContext, useEffect, useState, useLayoutEffect, useRef, useCallback } from "react";
import RuleLeaf, { SkeletonRuleLeaf } from "./QObject";
import { DnDCourse, Fulfillment } from "@/types";
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import { baseFetcher, postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { useDrop } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import { DarkBlueBackgroundSkeleton } from "../FourYearPlan/PanelCommon";
import { RuleTree, FaultyRuleTree, WhiteSpace, HEADER_DEFAULT_BUFFER } from "./ReqPanel";
import SatisfiedCheck from "../FourYearPlan/SatisfiedCheck";
import { ExpandedCoursesPanelContext } from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";
import { subscribeProposal, currentProposal } from "@/hooks/generateConfig";
import { parseQJson } from "./ruleUtils";
import { useSWRConfig } from "swr";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { containsRule, scrollToPlacement, subscribeRuleNav } from "@/hooks/requirementNav";

/** Whether a dragged course sits in the AP & transfer credit semester. */
const isTransferCredit = (course: DnDCourse) =>
  (course?.semester ?? course?.fulfillment?.semester) === TRANSFER_CREDIT_SEMESTER_KEY;

/** Course codes when a rule is nothing but a list of courses. Otherwise null. */
const listedCourseCodes = (node: any): string[] | null => {
  if (!node || typeof node !== "object") return null;
  if (node.type === "COURSE" && node.full_code) return [node.full_code];
  if (node.type === "LEAF" && node.key === "full_code" && node.value) return [String(node.value)];
  if (node.type === "OR" && Array.isArray(node.clauses) && node.clauses.length) {
    const codes: string[] = [];
    for (const clause of node.clauses) {
      const child = listedCourseCodes(clause);
      if (!child) return null;
      codes.push(...child);
    }
    return codes;
  }
  if (node.type === "AND" && Array.isArray(node.clauses)) {
    const codes: string[] = [];
    for (const clause of node.clauses) {
      if (clause?.type === "LEAF" && clause.key === "semester") continue;
      const child = listedCourseCodes(clause);
      if (!child) return null;
      codes.push(...child);
    }
    return codes.length ? codes : null;
  }
  return null;
};

const normalizeCourseText = (value: string) =>
  value.toUpperCase().replace(/-/g, " ").replace(/\s+/g, " ").trim();

/** A title like "ESE 2900 & ESE 2910" only repeats the courses already shown as chips. */
const titleRestatesCourses = (title: string, codes: string[]) => {
  const parts = normalizeCourseText(title).split(/\s*(?:&|\/|,|\bAND\b)\s*/).filter(Boolean);
  if (parts.length !== codes.length) return false;
  const want = codes.map(normalizeCourseText).sort();
  const got = [...parts].sort();
  return want.every((code, index) => code === got[index]);
};

const SuggestionChips = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  min-width: 0;
  max-width: 100%;
  align-items: center;
`;

const SuggestionChip = styled.button<{ $dashed?: boolean }>`
  font: inherit;
  font-size: var(--type-body);
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  cursor: pointer;
  border: 1px ${(props) => (props.$dashed ? "dashed" : "solid")} rgba(0, 0, 0, 0.18);
  background: #fff;
  color: #4b5563;

  &:hover {
    border-color: rgba(15, 118, 110, 0.55);
  }
`;

const RuleTitleWrapper = styled.div<{ $headerHeight?: number, $zIndex?: number, $done?: boolean }>`
  position: sticky;
  top: ${(props) => (props.$headerHeight || 0) + HEADER_DEFAULT_BUFFER}px;
  z-index: ${(props) => props.$zIndex || 995};
  margin-top: 4px;
  background: ${(props) => (props.$done ? "rgba(34, 197, 94, 0.06)" : "#fff")};
  color: #1f2937;
  border: 1px solid ${(props) => (props.$done ? "rgba(34, 197, 94, 0.25)" : "rgba(0, 0, 0, 0.08)")};
  border-radius: 6px;
  overflow: hidden;
`;

const RuleTitle = styled.div<{ $done?: boolean }>`
  position: relative;
  font-size: var(--type-body);
  font-weight: 700;
  line-height: 1.3;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  width: 100%;
  color: #1f2937;
  padding: 5px 8px;
  background: ${(props) => (props.$done ? "rgba(34, 197, 94, 0.06)" : "rgba(0, 0, 0, 0.035)")};

  > div:first-child {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
`;

const CountPill = styled.span<{ $done?: boolean }>`
  flex-shrink: 0;
  font-size: var(--type-body);
  font-weight: 700;
  color: ${(props) => (props.$done ? "#15803d" : "#64748b")};
  background: ${(props) => (props.$done ? "rgba(34, 197, 94, 0.12)" : "rgba(0, 0, 0, 0.04)")};
  border: 1px solid ${(props) => (props.$done ? "rgba(34, 197, 94, 0.25)" : "rgba(0, 0, 0, 0.08)")};
  border-radius: 8px;
  padding: 0 6px;
`;

const RuleLeafWrapper = styled.div<{ $isDroppable: boolean; $isOver: boolean; $scroll?: boolean }>`
  padding: 0;
  margin-left: 0;
  display: flex;
  justify-content: flex-start;
  flex-wrap: ${(props) => (props.$scroll ? "nowrap" : "wrap")};
  gap: 2px;
  align-items: center;
  flex: ${(props) => (props.$scroll ? "1 1 0" : "1 1 10rem")};
  min-width: ${(props) => (props.$scroll ? "0" : "min(100%, 10rem)")};
  max-width: 100%;
  overflow-x: ${(props) => (props.$scroll ? "auto" : "visible")};
  box-shadow: ${(props) =>
    props.$isOver && props.$isDroppable
      ? "0px 0px 0px 2px var(--selected-color);"
      : "none"};
  border-radius: 4px;
`;

const CusCourses = styled.div`
  font-weight: 700;
  font-size: var(--type-body);
  white-space: nowrap;
  color: #64748b;
`;

const Row = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const Indented = styled.div`
  margin-left: 10px;
  padding-left: 8px;
  min-width: 0;
  max-width: 100%;
  border-left: 2px solid rgba(0, 0, 0, 0.06);
`;

const Column = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0rem;
  min-width: 0;
  max-width: 100%;
`;

const Counts = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
  margin-left: 6px;
`;

const PickNWrapper = styled.div`
  margin-top: 4px;
  min-width: 0;
  max-width: 100%;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  overflow: hidden;
`;

const PickNTitle = styled.div`
  display: flex;
  align-items: center;
  font-weight: 700;
  font-size: var(--type-body);
  padding: 5px 8px;
  background: rgba(0, 0, 0, 0.035);
  justify-content: space-between;
`;

const LeafMain = styled.div<{ $scroll?: boolean }>`
  display: flex;
  flex: 1;
  min-width: 0;
  flex-wrap: ${(props) => (props.$scroll ? "nowrap" : "wrap")};
  align-items: center;
  gap: 4px;
  font-size: var(--type-body);
  font-weight: 600;
  line-height: 1.35;
`;

const Stem = styled.span<{ $scroll?: boolean }>`
  color: #1f2937;
  min-width: 0;
  ${(props) =>
    props.$scroll
      ? `
    flex: 0 1 auto;
    max-width: 46%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  `
      : "word-break: break-word;"}
`;

const Colon = styled.span`
  color: #94a3b8;
  font-weight: 600;
`;

const StatusMark = styled.span<{ $tone: "done" | "partial" | "open" }>`
  flex-shrink: 0;
  width: 12px;
  margin-top: 1px;
  text-align: center;
  font-weight: 800;
  line-height: 1.35;
  color: ${(props) =>
    props.$tone === "done" ? "#16a34a" : props.$tone === "partial" ? "#d97706" : "#94a3b8"};
`;

const OverrideTagWrapper = styled.div`
  position: relative;
  display: inline-flex;
`;

const OverrideTag = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: var(--type-body);
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
  font-size: var(--type-body);
`;

const OverridePopoverTitle = styled.div`
  font-weight: 600;
  font-size: var(--type-body);
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
  font-size: var(--type-body);
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
  font-size: var(--type-title);
  margin-bottom: 0.75rem;
  color: var(--modal-title-color, #333);
`;

const OverrideModalBody = styled.div`
  font-size: var(--type-body);
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
  font-size: var(--type-body);
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

const RuleLeafContainer = styled.div<{ $tone: "done" | "partial" | "open" }>`
  display: flex;
  flex-wrap: nowrap;
  align-items: flex-start;
  gap: 6px;
  min-width: 0;
  max-width: 100%;
  padding: 5px 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  background: ${(props) =>
    props.$tone === "done"
      ? "rgba(22, 163, 74, 0.04)"
      : props.$tone === "partial"
        ? "rgba(217, 119, 6, 0.08)"
        : "transparent"};
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
  const [proposal, setProposal] = useState(currentProposal());
  useEffect(() => subscribeProposal(() => setProposal(currentProposal())), []);
  useEffect(() => subscribeRuleNav((ruleId) => {
    if (rule.id === ruleId || containsRule(rule.rules, ruleId)) setCollapsed(false);
  }), [rule]);

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
    [createOrUpdate, satisfied, courseMatchesRule, rule.transfer_credit_allowed]
  );

  if (type === "LEAF") {
    const { fulfillments, unselectedFulfillments, cus, num } = ruleTree;
    const overrideFulfillments = fulfillments.filter(
      (f) => f.overrides?.includes(rule.id)
    );
    const codes = listedCourseCodes(rule.q_json);
    const hideTitle = !!(codes && titleRestatesCourses(rule.title || "", codes));
    const title = hideTitle ? null : rule.title;
    const scrollCourses = (codes?.length || 0) > 3;
    const tone = satisfied ? "done" : progress > 0 ? "partial" : "open";
    const suggestions = codes
      ? []
      : (proposal?.placements.filter((row) => row.rules.includes(rule.id)) || []);
    return (
      <RuleLeafContainer id={`rule-${rule.id}`} $tone={tone}>
        {overrideModal && (
          <OverrideModal
            fullCode={overrideModal.fullCode}
            ruleTitle={rule.title}
            onConfirm={handleOverrideConfirm}
            onCancel={() => setOverrideModal(null)}
            isLoading={overrideLoading}
          />
        )}
        <StatusMark $tone={tone}>{tone === "done" ? "✓" : tone === "partial" ? "◐" : "○"}</StatusMark>
        <LeafMain $scroll={scrollCourses}>
          {title && (
            <Stem $scroll={scrollCourses}>
              {title}
              <Colon>:</Colon>
            </Stem>
          )}
          <RuleLeafWrapper $isDroppable={canDrop} $isOver={isOver} $scroll={scrollCourses} ref={drop}>
            <RuleLeaf
              q_json={rule.q_json}
              rule={rule}
              fulfillmentsForRule={fulfillments}
              unselectedFulfillmentsForRule={unselectedFulfillments}
              satisfied={satisfied}
              activeDegreePlanId={activeDegreePlanId}
            />
          </RuleLeafWrapper>
          {suggestions.length > 0 && (
            <SuggestionChips>
              {suggestions.map((row) => (
                <SuggestionChip
                  key={row.slot_ids[0] || row.full_code || row.label}
                  type="button"
                  $dashed={row.kind !== "placement"}
                  title={row.semester ? "Show on the schedule" : undefined}
                  onClick={() => scrollToPlacement(row)}
                >
                  {(row.kind === "course" ? (row.short_label || row.label) : (row.full_code || row.label)).replace(/-/g, " ")}
                </SuggestionChip>
              ))}
            </SuggestionChips>
          )}
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
        </LeafMain>
        <Counts>
          {rule.credits != null && (
            <CusCourses>
              {cus}/{rule.credits}
            </CusCourses>
          )}
          {rule.num != null && (
            <CusCourses>
              {num}/{rule.num}
            </CusCourses>
          )}
        </Counts>
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
      <RuleTitleWrapper $done={progress >= 1} $headerHeight={headerHeight} $zIndex={zIndex} onClick={() => setCollapsed(!collapsed)} ref={myHeaderRef}>
        <RuleTitle $done={progress >= 1}>
          <div>
            {rule.title}
          </div>
          <CountPill $done={progress >= 1}>{(progress * 100).toFixed(0)}%</CountPill>
          {rule.rules.length && (
            <Icon style={{ color: "#64748b" }}>
              <i className={`fas fa-chevron-${collapsed ? "right" : "down"}`}></i>
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
