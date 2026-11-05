import {
  useContext,
  useMemo,
  useState,
  useRef,
  useEffect,
  useLayoutEffect,
  RefObject,
} from "react";
import { ConnectDragSource, useDragLayer } from "react-dnd";
import { Course, DegreePlan, DnDCourse, Fulfillment } from "@/types";
import { rulesByProgram, RuleInProgram } from "@/utils/programs";
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
import {
  PlannedCourseContainer,
  CloseIcon,
  CourseBadge,
  IconBadge,
  InfoIconButton,
  InfoPopoverWrapper,
  InfoPopover,
  PopoverSection,
  PopoverLabel,
  RuleList,
  RuleProgram,
  OverrideBadge,
  LevelDot,
  LevelDotButton,
  LevelMenu,
  LevelMenuHeading,
  LevelMenuItem,
  LevelMenuLabel,
  LevelMenuCheck,
  LevelMenuError,
  SwitchRuleButton,
  DisplacedBanner,
  Exclamation,
} from "./Course.styles";

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

const ExclamationIcon = ({ color }: { color: string }) => (
  <Exclamation $color={color}>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
      <path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zm0-384c13.3 0 24 10.7 24 24l0 112c0 13.3-10.7 24-24 24s-24-10.7-24-24l0-112c0-13.3 10.7-24 24-24zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z" />
    </svg>
  </Exclamation>
);

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

const RuleNames = ({ rules }: { rules: (RuleInProgram & { isOverride?: boolean })[] }) => (
  <RuleList>
    {rules.map((rule, i) => (
      <li key={i}>
        <RuleProgram>[{rule.program.code}]</RuleProgram> {rule.title}
        {rule.isOverride && (
          <OverrideBadge style={{ marginLeft: "0.35rem" }}>
            <i className="fas fa-star" /> override
          </OverrideBadge>
        )}
      </li>
    ))}
  </RuleList>
);

// Whether another card for the same course is being dragged, so this one can light up too.
const useIsDragRelated = (fullCode: string, isDragging: boolean) => {
  const sameCourseDragging = useDragLayer(
    (monitor) =>
      monitor.isDragging() &&
      (monitor.getItem() as { full_code?: string } | null)?.full_code === fullCode
  );
  return sameCourseDragging && !isDragging;
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

  const planRules = useMemo(
    () => (degreePlanDetail ? rulesByProgram(degreePlanDetail) : new Map<number, RuleInProgram>()),
    [degreePlanDetail]
  );
  const unselectedRuleNames = useMemo(
    () =>
      (fulfillment?.unselected_rules ?? [])
        .map((id) => planRules.get(id))
        .filter((rule): rule is RuleInProgram => !!rule),
    [fulfillment?.unselected_rules, planRules]
  );
  const selectedRuleNames = useMemo(() => {
    const overrides = new Set(fulfillment?.overrides ?? []);
    return (fulfillment?.rules ?? []).flatMap((id) => {
      const rule = planRules.get(id);
      return rule ? [{ ...rule, isOverride: overrides.has(id) }] : [];
    });
  }, [fulfillment?.rules, fulfillment?.overrides, planRules]);
  const isDragRelated = useIsDragRelated(course.full_code, isDragging);

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
  const shouldShowCouldAlsoCountFor = unselectedRuleNames.length > 0;
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
            $isDragRelated={isDragRelated}
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
            <CourseBadge className="course-badge">
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
                          <RuleNames rules={selectedRuleNames} />
                        </PopoverSection>
                      )}
                      {shouldShowCouldAlsoCountFor && (
                        <PopoverSection>
                          <PopoverLabel>Could also count for</PopoverLabel>
                          <RuleNames rules={unselectedRuleNames} />
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
                            <div style={{ marginTop: "0.35rem", color: "var(--error-color)" }}>
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
          $isDragRelated={isDragRelated}
          ref={dragRef}
          className={className}
        >
          <CourseBadge className="course-badge">
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
                          <div style={{ marginTop: "0.35rem", color: "var(--error-color)" }}>
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
