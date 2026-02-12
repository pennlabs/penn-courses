import { useMemo, useState, useRef, useEffect } from "react";
import { ConnectDragSource } from "react-dnd";
import { GrayIcon, Icon } from "@/components/common/bulma_derived_components";
import styled from "@emotion/styled";
import { Course, DegreePlan, DnDCourse, Fulfillment, Rule } from "@/types";
import { ReviewPanelTrigger } from "@/components/Infobox/ReviewPanel";
import { Draggable } from "@/components/common/DnD";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { Tooltip } from "react-tooltip";
import useSWR from "swr";

const DOUBLE_COUNT_ERROR_MESSAGE =
  "This course is being illegally double counted in your plan!";
const COURSE_BORDER_RADIUS = "9px";

export const BaseCourseContainer = styled.div<{
  $isDragging?: boolean;
  $isUsed: boolean;
  $isDisabled: boolean;
}>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  border-radius: ${COURSE_BORDER_RADIUS};
  padding: 0.75rem;
  text-wrap: nowrap;
  cursor: ${(props) =>
    props.$isDisabled || props.$isUsed ? "not-allowed" : "grab"};
  opacity: ${(props) => (props.$isDisabled || props.$isDragging ? 0.7 : 1)};
  background-color: ${(props) =>
    props.$isDragging ? "#4B9AE7" : "var(--background-grey)"};
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
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  padding: 0.75rem 1rem;
  z-index: 10000;
  min-width: 220px;
  max-width: 350px;
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

const formatSemester = (semester: string | null): string => {
  if (!semester) return "";
  if (semester === TRANSFER_CREDIT_SEMESTER_KEY) return "AP & Transfer Credit";
  const year = semester.slice(0, 4);
  const term = semester.slice(4);
  return `${term === "A" ? "Spring" : term === "B" ? "Summer" : "Fall"} ${year}`;
};

/** Recursively flattens a rule tree into an id→title map */
const flattenRules = (rules: Rule[]): Map<number, string> => {
  const map = new Map<number, string>();
  const traverse = (ruleList: Rule[]) => {
    for (const rule of ruleList) {
      if (rule.title) {
        map.set(rule.id, rule.title);
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
  removeCourse,
  isUsed = false,
  isDisabled = false,
  className,
  onClick,
  isDragging,
  dragRef,
}: DraggableComponentProps) => {
  // Look up rule titles for unselected rules (uses SWR cache from ReqPanel)
  const { data: degreePlanDetail } = useSWR<DegreePlan>(
    fulfillment?.degree_plan
      ? `/api/degree/degreeplans/${fulfillment.degree_plan}`
      : null
  );

  const unselectedRuleNames = useMemo(() => {
    if (!fulfillment?.unselected_rules?.length || !degreePlanDetail?.degrees) return [];
    const ruleMap = new Map<number, string>();
    for (const degree of degreePlanDetail.degrees) {
      flattenRules(degree.rules).forEach((title, id) => ruleMap.set(id, title));
    }
    return fulfillment.unselected_rules
      .map(id => ruleMap.get(id))
      .filter((t): t is string => !!t);
  }, [fulfillment?.unselected_rules, degreePlanDetail]);

  const [infoOpen, setInfoOpen] = useState(false);
  const infoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!infoOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (infoRef.current && !infoRef.current.contains(e.target as Node)) {
        setInfoOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [infoOpen]);

  const hasSemester = !!fulfillment?.semester && fulfillment.semester !== "";
  const hasInfoContent = hasSemester || unselectedRuleNames.length > 0;

  if (!!fulfillment) {
    return (
      <Draggable isDragging={isDragging} onClick={onClick}>
        <ReviewPanelTrigger full_code={course.full_code} triggerType="click">
          <PlannedCourseContainer
            $isDragging={isDragging}
            $isUsed={isUsed}
            $isDisabled={isDisabled}
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
              {course.full_code.replace("-", " ")}
              {hasInfoContent && (
                <InfoPopoverWrapper ref={infoRef}>
                  <InfoIconButton onClick={(e) => { e.stopPropagation(); setInfoOpen(!infoOpen); }}>
                    <i className="fas fa-info-circle"></i>
                  </InfoIconButton>
                  {infoOpen && (
                    <InfoPopover>
                      {hasSemester && (
                        <PopoverSection>
                          <PopoverLabel>Semester</PopoverLabel>
                          {formatSemester(fulfillment.semester)}
                        </PopoverSection>
                      )}
                      {unselectedRuleNames.length > 0 && (
                        <PopoverSection>
                          <PopoverLabel>Could also count for</PopoverLabel>
                          <RuleList>
                            {unselectedRuleNames.map((name, i) => <li key={i}>{name}</li>)}
                          </RuleList>
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
          ref={dragRef}
          className={className}
        >
          <CourseBadge>{course.full_code.replace("-", " ")}</CourseBadge>
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
