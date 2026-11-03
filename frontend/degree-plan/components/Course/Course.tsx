import {
  useContext,
  useMemo,
  useState,
  useRef,
  useEffect,
  useLayoutEffect,
  RefObject,
} from "react";
import { ConnectDragSource } from "react-dnd";
import { GrayIcon, Icon } from "@/components/common/bulma_derived_components";
import styled from "@emotion/styled";
import { Course, Degree, DegreePlan, DnDCourse, Fulfillment, Rule } from "@/types";
import { ReviewPanelTrigger } from "@/components/Infobox/ReviewPanel";
import { Draggable } from "@/components/common/DnD";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { Tooltip } from "react-tooltip";
import useSWR from "swr";
import { ItemTypes } from "@/components/Dock/dnd/constants";
import { postFetcher } from "@/hooks/swrcrud";
import { useSWRConfig } from "swr";
import ToastContext from "@/components/Toast/Toast";

const DOUBLE_COUNT_ERROR_MESSAGE =
  "This course is being illegally double counted in your plan!";
// Which of a submatriculant's degrees a course counts toward, as the backend names them.
// Each level has a colour, used for the status dot on the card and in the menu that sets it;
// a null colour draws a hollow dot for the unmarked state.
const LEVEL_OPTIONS: {
  value: Fulfillment["level"];
  label: string;
  title: string;
  color: string | null;
}[] = [
  {
    value: null,
    label: "Not marked (either)",
    title: "Not marked: may count toward either degree",
    color: null,
  },
  {
    value: "UNDERGRADUATE",
    label: "Bachelors only",
    title: "Counts toward your bachelors only",
    color: "#3b82c4",
  },
  {
    value: "GRADUATE",
    label: "Masters only",
    title: "Counts toward your masters only",
    color: "#5b61b8",
  },
  {
    value: "SHARED",
    label: "Both (double counted)",
    title: "Double counted toward both degrees",
    color: "#3a8a5f",
  },
];
const levelOption = (level: Fulfillment["level"] | undefined) =>
  LEVEL_OPTIONS.find((option) => option.value === (level ?? null)) ?? LEVEL_OPTIONS[0];
// Only a course numbered 5000 or above can sit on a masters record, matching the backend's
// MIN_GRADUATE_COURSE_NUMBER, so lower-numbered courses have no level to choose.
const MIN_GRADUATE_COURSE_NUMBER = 5000;
const isGraduateCourse = (fullCode: string | undefined) => {
  const match = /-(\d+)/.exec(fullCode ?? "");
  return !!match && parseInt(match[1], 10) >= MIN_GRADUATE_COURSE_NUMBER;
};

// Closes a popover on any mousedown outside `ref` while it is open.
const useClickOutside = (
  open: boolean,
  ref: RefObject<HTMLElement>,
  setOpen: (open: boolean) => void
) => {
  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open, ref, setOpen]);
};

// Marks the region a popover may occupy; see useAnchoredPopover.
export const POPOVER_BOUNDS_ATTRIBUTE = "data-popover-bounds";

// Positions a `position: fixed` popover just below its anchor, clamped within its bounds and
// flipped above the anchor when it would overflow the bottom. The bounds are the nearest
// ancestor marked with POPOVER_BOUNDS_ATTRIBUTE (the plan body, which stops above the footer
// and dock), or the viewport when there is none. A fixed element does not move with a
// scrolling panel, so the position is recomputed on every scroll and resize while the
// popover is open; otherwise it would stay put on screen as its anchor slid away.
const useAnchoredPopover = (
  open: boolean,
  anchorRef: RefObject<HTMLElement>,
  popoverRef: RefObject<HTMLElement>
) => {
  useLayoutEffect(() => {
    if (!open) return;
    const position = () => {
      const el = popoverRef.current;
      const anchor = anchorRef.current;
      if (!el || !anchor) return;
      const anchorRect = anchor.getBoundingClientRect();
      const boundsRect = anchor
        .closest(`[${POPOVER_BOUNDS_ATTRIBUTE}]`)
        ?.getBoundingClientRect();
      const padding = 8;
      const minTop = (boundsRect?.top ?? 0) + padding;
      const maxBottom = (boundsRect?.bottom ?? window.innerHeight) - padding;
      const minLeft = (boundsRect?.left ?? 0) + padding;
      const maxRight = (boundsRect?.right ?? window.innerWidth) - padding;

      let top = anchorRect.bottom + 8;
      let left = anchorRect.left;

      // Measure the popover so we can clamp
      el.style.top = `${top}px`;
      el.style.left = `${left}px`;
      const popRect = el.getBoundingClientRect();

      if (popRect.right > maxRight) {
        left -= popRect.right - maxRight;
      }
      if (left < minLeft) {
        left = minLeft;
      }
      if (top + popRect.height > maxBottom) {
        top = anchorRect.top - popRect.height - 8;
      }
      if (top < minTop) {
        top = minTop;
      }

      el.style.top = `${top}px`;
      el.style.left = `${left}px`;
    };

    position();
    // Capture phase so scrolls inside nested panels are seen, not just the window's.
    document.addEventListener("scroll", position, true);
    window.addEventListener("resize", position);
    return () => {
      document.removeEventListener("scroll", position, true);
      window.removeEventListener("resize", position);
    };
  }, [open, anchorRef, popoverRef]);
};
const COURSE_BORDER_RADIUS = "9px";
const HIGHLIGHT_VARIANT_COLORS = {
  selected: "#E6F4EA",
  unselected: "#FFF7D6",
} as const;

export const BaseCourseContainer = styled.div<{
  $isDragging?: boolean;
  $isUsed: boolean;
  $isDisabled: boolean;
  $highlightVariant?: "selected" | "unselected";
}>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  border-radius: ${COURSE_BORDER_RADIUS};
  padding: 0.75rem;
  text-wrap: nowrap;
  cursor: ${(props) => (props.$isDisabled ? "not-allowed" : "grab")};
  opacity: ${(props) => (props.$isDisabled || props.$isDragging ? 0.7 : 1)};
  background-color: ${(props) =>
    props.$isDragging
      ? "#4B9AE7"
      : (props.$highlightVariant &&
          HIGHLIGHT_VARIANT_COLORS[props.$highlightVariant]) ||
        "var(--background-grey)"};
  box-shadow: rgba(0, 0, 0, 0.01) 0px 6px 5px 0px,
    rgba(0, 0, 0, 0.04) 0px 0px 0px 1px;
`;

export const PlannedCourseContainer = styled(BaseCourseContainer)`
  width: 100%;
  position: relative;
  opacity: ${(props) => (props.$isDragging ? 0.5 : 1)};

  .close-button {
    padding-left: 1rem;
    padding-right: 10px;
    margin-top: auto;
    margin-bottom: auto;
    height: 100%;
    align-items: center;
    opacity: 0.6;
  }

  .illegal-icon {
    padding-right: 0.5rem;
    margin-top: auto;
    margin-bottom: auto;
  }

  &:hover {
    .close-button {
      opacity: unset;
    }
  }
`;

const CloseIcon = styled(GrayIcon)<{ $hidden: boolean }>`
  visibility: ${(props) => (props.$hidden ? "hidden" : "visible")};
  cursor: pointer;
`;

export const CourseXButton = ({
  onClick,
  hidden,
}: {
  onClick?: (e: React.MouseEvent<HTMLInputElement>) => void;
  hidden: boolean;
}) => (
  <CloseIcon className="close-button" onClick={onClick} $hidden={hidden}>
    <i className="fas fa-times"></i>
  </CloseIcon>
);

interface DraggableComponentProps {
  courseType: string;
  course: DnDCourse;
  removeCourse: (course: Course["id"]) => void;
  semester?: Course["semester"];
  isUsed: boolean;
  isDisabled: boolean;
  isDragging: boolean;
  fulfillment?: Fulfillment;
  isUnselectedRule?: boolean;
  isOverride?: boolean;
  ruleId?: number;
  activeDegreePlanId?: number;
  className?: string;
  onClick?: (arg0: React.MouseEvent<HTMLInputElement>) => void;
  dragRef: ConnectDragSource;
}

export const SkeletonCourse = () => (
  <PlannedCourseContainer $isUsed={false} $isDisabled={false}>
    <Skeleton width="5em" />
  </PlannedCourseContainer>
);

const CourseBadge = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.25rem;
`;

const IconBadge = styled.div`
  padding: 0.2rem;
  border-radius: 5px;
  border: 1px solid #d8d8d8;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.07rem;
  background-color: transparent;

  p {
    font-size: 14px;
    font-weight: bold;
  }
`;

const InfoIconButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.2rem;
  display: flex;
  align-items: center;
  color: #aaa;
  font-size: 0.85rem;
  margin-left: 0.25rem;

  &:hover {
    color: #555;
  }
`;

const InfoPopoverWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const InfoPopover = styled.div`
  position: fixed;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  padding: 0.75rem 1rem;
  z-index: 10000;
  min-width: 220px;
  max-width: min(350px, calc(100vw - 16px));
  width: max-content;
  text-align: left;
  font-size: 0.85rem;
  color: #333;
  white-space: normal;
  word-wrap: break-word;
`;

const PopoverSection = styled.div`
  overflow: visible;

  &:not(:last-child) {
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #eee;
  }
`;

const PopoverLabel = styled.div`
  font-weight: 600;
  font-size: 0.7rem;
  color: #888;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
`;

const RuleList = styled.ul`
  margin: 0;
  padding-left: 1rem;
  list-style-position: outside;

  li {
    margin-bottom: 0.15rem;
    padding-left: 0.15rem;
  }
`;

const OverrideBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.7rem;
  color: #b8860b;
  font-weight: 600;
`;

// A Gmail-style status dot: the course's level at a glance, and the handle for changing it.
const LevelDot = styled.span<{ $color: string | null }>`
  display: inline-block;
  width: 0.6rem;
  height: 0.6rem;
  flex-shrink: 0;
  border-radius: 50%;
  box-sizing: border-box;
  background: ${({ $color }) => $color ?? "transparent"};
  border: 2px solid ${({ $color }) => $color ?? "#b5b5b5"};
`;

const LevelDotButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.3rem;
  margin-right: 0.1rem;
  border: none;
  border-radius: 50%;
  background: none;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: rgba(0, 0, 0, 0.07);
  }

  &:disabled {
    cursor: default;
  }
`;

const LevelMenu = styled.div`
  position: fixed;
  z-index: 10000;
  min-width: 210px;
  padding: 0.3rem 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  text-align: left;
  white-space: nowrap;
`;

const LevelMenuHeading = styled.div`
  padding: 0.3rem 0.9rem 0.4rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.03em;
`;

const LevelMenuItem = styled.button<{ $active: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.45rem 0.9rem;
  border: none;
  background: ${({ $active }) => ($active ? "#f1f3f4" : "none")};
  color: #333;
  font-size: 0.85rem;
  text-align: left;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: #e8eaed;
  }

  &:disabled {
    cursor: default;
    opacity: 0.6;
  }
`;

const LevelMenuLabel = styled.span`
  flex-grow: 1;
`;

const LevelMenuCheck = styled.i`
  font-size: 0.75rem;
  color: #555;
`;

const LevelMenuError = styled.div`
  padding: 0.3rem 0.9rem 0.4rem;
  font-size: 0.8rem;
  color: #a94442;
  white-space: normal;
`;

const SwitchRuleButton = styled.button`
  border: 1px solid #d7cc86;
  border-radius: 6px;
  background: #fff7d6;
  color: #645500;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.35rem 0.55rem;
  cursor: pointer;

  &:disabled {
    opacity: 0.7;
    cursor: default;
  }
`;

const DisplacedBanner = styled.div`
  margin-top: 0.4rem;
  padding: 0.35rem 0.55rem;
  border-radius: 6px;
  background: #fff3e0;
  border: 1px solid #e0c080;
  color: #7a4f00;
  font-size: 0.78rem;
  line-height: 1.35;
`;

const ExclamationIcon = ({ color }: { color: string }) => {
  const Exclamation = styled(Icon)`
    width: 1rem;
    height: 1rem;
    display: flex;
    fill: ${color};
  `;

  return (
    <Exclamation>
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
        <path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zm0-384c13.3 0 24 10.7 24 24l0 112c0 13.3-10.7 24-24 24s-24-10.7-24-24l0-112c0-13.3 10.7-24 24-24zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z" />
      </svg>
    </Exclamation>
  );
};

const SemesterIcon = ({ semester }: { semester: string | null }) => {
  if (!semester) return <div></div>;
  const year =
    semester === TRANSFER_CREDIT_SEMESTER_KEY ? "AP" : semester.substring(2, 4);
  const sem = semester.substring(4);

  return (
    <IconBadge>
      <p>{year}</p>
      {sem === "A" && <i className="spring-icon"></i>}
      {sem === "B" && <i className="summer-icon"></i>}
      {sem === "C" && <i className="fall-icon"></i>}
    </IconBadge>
  );
};

const formatDegreeName = (degree: Degree): string => {
  const {
    degree: degreeType,
    major,
    concentration,
    major_name: majorName,
    concentration_name: concentrationName,
  } = degree;

  if (degreeType && major) {
    return `${degreeType} ${major}${concentration ? ` (${concentration})` : ""}`;
  }
  return `${degreeType} in ${majorName}${concentration ? ` (${concentrationName})` : ""}`;
};

/** Recursively flattens a rule tree into an id→(title, degree) map */
const flattenRules = (
  rules: Rule[],
  degreeName: string
): Map<number, { title: string; degreeName: string }> => {
  const map = new Map<number, { title: string; degreeName: string }>();
  const traverse = (ruleList: Rule[]) => {
    for (const rule of ruleList) {
      if (rule.title) {
        map.set(rule.id, { title: rule.title, degreeName });
      }
      if (rule.rules?.length) {
        traverse(rule.rules);
      }
    }
  };
  traverse(rules);
  return map;
};

const CourseComponent = ({
  courseType,
  course,
  fulfillment,
  isUnselectedRule = false,
  isOverride = false,
  ruleId,
  activeDegreePlanId,
  removeCourse,
  isUsed = false,
  isDisabled = false,
  className,
  onClick,
  isDragging,
  dragRef,
}: DraggableComponentProps) => {
  const { mutate } = useSWRConfig();
  const showToast = useContext(ToastContext);

  // Look up rule titles for unselected rules (uses SWR cache from ReqPanel)
  const { data: degreePlanDetail } = useSWR<DegreePlan>(
    fulfillment?.degree_plan
      ? `/api/degree/degreeplans/${fulfillment.degree_plan}`
      : null
  );

  const unselectedRuleNames = useMemo(() => {
    if (!fulfillment?.unselected_rules?.length || !degreePlanDetail?.degrees) return [];
    const ruleMap = new Map<number, { title: string; degreeName: string }>();
    for (const degree of degreePlanDetail.degrees) {
      const degreeName = formatDegreeName(degree);
      flattenRules(degree.rules, degreeName).forEach((ruleInfo, id) =>
        ruleMap.set(id, ruleInfo)
      );
    }
    return fulfillment.unselected_rules
      .map(id => ruleMap.get(id))
      .filter((t): t is { title: string; degreeName: string } => !!t);
  }, [fulfillment?.unselected_rules, degreePlanDetail]);
  const overrideSet = useMemo(
    () => new Set(fulfillment?.overrides ?? []),
    [fulfillment?.overrides]
  );
  const selectedRuleNames = useMemo(() => {
    if (!fulfillment?.rules?.length || !degreePlanDetail?.degrees) return [];
    const ruleMap = new Map<number, { title: string; degreeName: string }>();
    for (const degree of degreePlanDetail.degrees) {
      const degreeName = formatDegreeName(degree);
      flattenRules(degree.rules, degreeName).forEach((ruleInfo, id) =>
        ruleMap.set(id, ruleInfo)
      );
    }
    return fulfillment.rules
      .map(id => {
        const info = ruleMap.get(id);
        if (!info) return null;
        return { ...info, isOverride: overrideSet.has(id) };
      })
      .filter((t): t is { title: string; degreeName: string; isOverride: boolean } => !!t);
  }, [fulfillment?.rules, degreePlanDetail, overrideSet]);

  // Only a plan with a masters degree has anything to mark a course's level against, and the
  // mark belongs to the course in the plan, not to its copies in the requirements panel.
  const showLevel =
    !!fulfillment &&
    courseType !== ItemTypes.COURSE_IN_REQ &&
    isGraduateCourse(fulfillment.full_code);
  // A planned course is not always handed the active plan's id, but its fulfillment knows
  // which plan it belongs to, and that is the plan whose record the level is set on.
  const levelPlanId = activeDegreePlanId ?? fulfillment?.degree_plan;
  const canSetLevel =
    showLevel &&
    !!levelPlanId &&
    !!degreePlanDetail?.degrees.some((degree) => degree.degree === "MSE");
  // A course already marked for the masters record keeps its dot even where it can't be
  // changed, so the mark stays visible; otherwise the dot only appears where it can be set.
  const currentLevel = levelOption(fulfillment?.level);
  const showLevelDot =
    canSetLevel ||
    (showLevel && (fulfillment?.level === "GRADUATE" || fulfillment?.level === "SHARED"));
  const [settingLevel, setSettingLevel] = useState(false);
  const [levelError, setLevelError] = useState<string | null>(null);
  const [levelOpen, setLevelOpen] = useState(false);
  const levelRef = useRef<HTMLDivElement>(null);
  const levelMenuRef = useRef<HTMLDivElement>(null);
  useClickOutside(levelOpen, levelRef, setLevelOpen);
  useAnchoredPopover(levelOpen, levelRef, levelMenuRef);

  const [infoOpen, setInfoOpen] = useState(false);
  const [switchingRule, setSwitchingRule] = useState(false);
  const [switchError, setSwitchError] = useState<string | null>(null);
  const [displacedMessage, setDisplacedMessage] = useState<string | null>(null);
  const infoRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  useClickOutside(infoOpen, infoRef, setInfoOpen);
  useAnchoredPopover(infoOpen, infoRef, popoverRef);

  const hasSemester = !!fulfillment?.semester && fulfillment.semester !== "";
  const courseSemester =
    "semester" in course
      ? (course as DnDCourse & { semester?: string | null }).semester
      : null;
  const displaySemester = fulfillment?.semester || courseSemester || null;
  const showSemesterOnCard =
    courseType === ItemTypes.COURSE_IN_REQ && !!displaySemester;
  const shouldShowSwitchHint =
    courseType === ItemTypes.COURSE_IN_REQ && isUnselectedRule;
  const shouldShowCouldAlsoCountFor =
    courseType === ItemTypes.COURSE_IN_REQ && unselectedRuleNames.length > 0;
  const hasInfoContent =
    hasSemester ||
    selectedRuleNames.length > 0 ||
    shouldShowCouldAlsoCountFor ||
    shouldShowSwitchHint ||
    !!displacedMessage;

  const handleSetLevel = async (level: Fulfillment["level"]) => {
    if (!levelPlanId || !fulfillment || settingLevel) return;
    setLevelOpen(false);
    if (level === currentLevel.value) return;

    const replaceWith =
      (updated: Fulfillment) =>
      (fulfillments: Fulfillment[] = []) =>
        fulfillments.map((f) => (f.full_code === updated.full_code ? updated : f));

    setSettingLevel(true);
    setLevelError(null);
    try {
      await mutate(
        `/api/degree/degreeplans/${levelPlanId}/fulfillments`,
        async (fulfillments?: Fulfillment[]) => {
          const updated: Fulfillment = await postFetcher(
            `/api/degree/degreeplans/${levelPlanId}/fulfillments/${fulfillment.full_code}/level`,
            { level }
          );
          return replaceWith(updated)(fulfillments);
        },
        {
          optimisticData: replaceWith({ ...fulfillment, level }),
          rollbackOnError: true,
          // A level change reallocates only this course, so the response row is the whole update
          revalidate: false,
        }
      );
    } catch {
      setLevelError("Could not change this course's level right now.");
      setLevelOpen(true);
    } finally {
      setSettingLevel(false);
    }
  };
  const highlightVariant =
    courseType === ItemTypes.COURSE_IN_REQ
      ? isUsed
        ? "selected"
        : isUnselectedRule
          ? "unselected"
          : undefined
      : undefined;

  const handleSwitchRule = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!activeDegreePlanId || !ruleId || switchingRule) return;
    try {
      setSwitchingRule(true);
      setSwitchError(null);
      setDisplacedMessage(null);
      const endpoint = `/api/degree/degreeplans/${activeDegreePlanId}/fulfillments/${course.full_code}/switch-rule`;
      const res = await postFetcher(endpoint, { rule_id: ruleId });
      await Promise.all([
        mutate(`/api/degree/degreeplans/${activeDegreePlanId}/fulfillments`),
        mutate(`/api/degree/degreeplans/${activeDegreePlanId}`),
      ]);

      const displaced: { full_code: string; removed: boolean }[] =
        res?.displaced ?? [];
      if (displaced.length > 0) {
        const msgs = displaced.map((d) => {
          const code = d.full_code.replace("-", " ");
          return d.removed
            ? `${code} was removed (it no longer fulfills any rules).`
            : `${code} was displaced from this rule.`;
        });
        const message = msgs.join(" ");
        setDisplacedMessage(message);
        showToast(message, false);
        setTimeout(() => {
          setDisplacedMessage(null);
          setInfoOpen(false);
        }, 5000);
      } else {
        setInfoOpen(false);
      }
    } catch {
      setSwitchError("Could not switch this course right now.");
    } finally {
      setSwitchingRule(false);
    }
  };

  if (!!fulfillment) {
    return (
      <Draggable isDragging={isDragging} onClick={onClick}>
        <ReviewPanelTrigger full_code={course.full_code} triggerType="click">
          <PlannedCourseContainer
            $isDragging={isDragging}
            $isUsed={isUsed}
            $isDisabled={isDisabled}
            $highlightVariant={highlightVariant}
            ref={dragRef}
            className={className}
          >
            {!fulfillment?.legal && (
              <div style={{ paddingRight: "5px" }}>
                <a
                  data-tooltip-id={fulfillment.full_code + courseType}
                  data-tooltip-content={DOUBLE_COUNT_ERROR_MESSAGE}
                >
                  <ExclamationIcon color={"#E66161"} />
                </a>
                <Tooltip 
                  id={fulfillment.full_code + courseType} 
                  place="top" 
                  style={{ zIndex: 9999 }}
                />
              </div>
            )}
            <CourseBadge>
              {showLevelDot && (
                <InfoPopoverWrapper
                  ref={levelRef}
                  title={
                    canSetLevel
                      ? `${currentLevel.title}. Click to change.`
                      : currentLevel.title
                  }
                >
                  <LevelDotButton
                    type="button"
                    disabled={!canSetLevel}
                    aria-label="Which degree this course counts toward"
                    aria-haspopup="menu"
                    aria-expanded={levelOpen}
                    onClick={(e) => {
                      e.stopPropagation();
                      setLevelOpen(!levelOpen);
                    }}
                  >
                    <LevelDot $color={currentLevel.color} />
                  </LevelDotButton>
                  {levelOpen && (
                    <LevelMenu
                      ref={levelMenuRef}
                      role="menu"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <LevelMenuHeading>Counts toward</LevelMenuHeading>
                      {LEVEL_OPTIONS.map((option) => {
                        const active = option.value === currentLevel.value;
                        return (
                          <LevelMenuItem
                            key={option.value ?? "none"}
                            type="button"
                            role="menuitemradio"
                            aria-checked={active}
                            $active={active}
                            disabled={settingLevel}
                            onClick={() => handleSetLevel(option.value)}
                          >
                            <LevelDot $color={option.color} />
                            <LevelMenuLabel>{option.label}</LevelMenuLabel>
                            {active && <LevelMenuCheck className="fas fa-check" />}
                          </LevelMenuItem>
                        );
                      })}
                      {levelError && <LevelMenuError>{levelError}</LevelMenuError>}
                    </LevelMenu>
                  )}
                </InfoPopoverWrapper>
              )}
              {course.full_code.replace("-", " ")}
              {isOverride && (
                <OverrideBadge
                  data-tooltip-id={`override-${fulfillment.full_code}-${ruleId}`}
                  data-tooltip-content="Manual override"
                >
                  <i className="fas fa-star" />
                </OverrideBadge>
              )}
              {isOverride && (
                <Tooltip
                  id={`override-${fulfillment.full_code}-${ruleId}`}
                  place="top"
                  style={{ zIndex: 9999 }}
                />
              )}
              {showSemesterOnCard && (
                <SemesterIcon semester={displaySemester} />
              )}
              {hasInfoContent && (
                <InfoPopoverWrapper ref={infoRef}>
                  <InfoIconButton onClick={(e) => { e.stopPropagation(); setInfoOpen(!infoOpen); }}>
                    <i className="fas fa-info-circle"></i>
                  </InfoIconButton>
                  {infoOpen && (
                    <InfoPopover ref={popoverRef}>
                      {/* {hasSemester && (
                        <PopoverSection>
                          <PopoverLabel>Semester</PopoverLabel>
                          {formatSemester(fulfillment.semester)}
                        </PopoverSection>
                      )} */}
                      {selectedRuleNames.length > 0 && (
                        <PopoverSection>
                          <PopoverLabel>Currently counts for</PopoverLabel>
                          <RuleList>
                            {selectedRuleNames.map((ruleInfo, i) => (
                              <li key={i}>
                                [{ruleInfo.degreeName}] {ruleInfo.title}
                                {ruleInfo.isOverride && (
                                  <OverrideBadge style={{ marginLeft: "0.35rem" }}>
                                    <i className="fas fa-star" /> override
                                  </OverrideBadge>
                                )}
                              </li>
                            ))}
                          </RuleList>
                        </PopoverSection>
                      )}
                      {shouldShowCouldAlsoCountFor && (
                        <PopoverSection>
                          <PopoverLabel>Could also count for</PopoverLabel>
                          <RuleList>
                            {unselectedRuleNames.map((ruleInfo, i) => (
                              <li key={i}>
                                [{ruleInfo.degreeName}] {ruleInfo.title}
                              </li>
                            ))}
                          </RuleList>
                        </PopoverSection>
                      )}
                      
                      {shouldShowSwitchHint && (
                        <PopoverSection>
                          <PopoverLabel>Tip</PopoverLabel>
                          You can switch this course to count for this rule.
                          <div style={{ marginTop: "0.5rem" }}>
                            <SwitchRuleButton onClick={handleSwitchRule} disabled={switchingRule}>
                              {switchingRule ? "Switching..." : "Count this course for this rule"}
                            </SwitchRuleButton>
                          </div>
                          {switchError && (
                            <div style={{ marginTop: "0.35rem", color: "#a94442" }}>
                              {switchError}
                            </div>
                          )}
                        </PopoverSection>
                      )}
                      {displacedMessage && (
                        <PopoverSection>
                          <PopoverLabel>Displaced</PopoverLabel>
                          <DisplacedBanner>{displacedMessage}</DisplacedBanner>
                        </PopoverSection>
                      )}
                    </InfoPopover>
                  )}
                </InfoPopoverWrapper>
              )}
            </CourseBadge>
            {isUsed && (
              <CourseXButton
                onClick={(e) => {
                  removeCourse(course.full_code);
                  e.stopPropagation();
                }}
                hidden={false}
              />
            )}
          </PlannedCourseContainer>
        </ReviewPanelTrigger>
      </Draggable>
    );
  }
  return (
    <Draggable isDragging={isDragging} onClick={onClick}>
      <ReviewPanelTrigger full_code={course.full_code} triggerType="click">
        <PlannedCourseContainer
          $isDragging={isDragging}
          $isUsed={isUsed}
          $isDisabled={isDisabled}
          $highlightVariant={highlightVariant}
          ref={dragRef}
          className={className}
        >
          <CourseBadge>
            {course.full_code.replace("-", " ")}
            {showSemesterOnCard && (
              <SemesterIcon semester={displaySemester} />
            )}
            {hasInfoContent && (
              <InfoPopoverWrapper ref={infoRef}>
                <InfoIconButton onClick={(e) => { e.stopPropagation(); setInfoOpen(!infoOpen); }}>
                  <i className="fas fa-info-circle"></i>
                </InfoIconButton>
                {infoOpen && (
                  <InfoPopover ref={popoverRef}>
                    {shouldShowSwitchHint && (
                      <PopoverSection>
                        <PopoverLabel>Tip</PopoverLabel>
                        You can switch this course to count for this rule.
                        <div style={{ marginTop: "0.5rem" }}>
                          <SwitchRuleButton onClick={handleSwitchRule} disabled={switchingRule}>
                            {switchingRule ? "Switching..." : "Count this course for this rule"}
                          </SwitchRuleButton>
                        </div>
                        {switchError && (
                          <div style={{ marginTop: "0.35rem", color: "#a94442" }}>
                            {switchError}
                          </div>
                        )}
                      </PopoverSection>
                    )}
                  </InfoPopover>
                )}
              </InfoPopoverWrapper>
            )}
          </CourseBadge>
          {isUsed && (
            <CourseXButton
              onClick={(e) => {
                removeCourse(course.full_code);
                e.stopPropagation();
              }}
              hidden={false}
            />
          )}
        </PlannedCourseContainer>
      </ReviewPanelTrigger>
    </Draggable>
  );
};

export default CourseComponent;
