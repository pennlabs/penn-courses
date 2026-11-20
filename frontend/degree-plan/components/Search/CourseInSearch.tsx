import React from "react";
import styled from "@emotion/styled";
import { useDrag } from "react-dnd";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { useCourseDragPreview } from "@/components/common/CourseDragPreview";
import { ItemTypes } from "@/components/Dock/dnd/constants";
import { ReviewPanelTrigger } from "@/components/Infobox/ReviewPanel";
import { Course as CourseType, DnDCourse, Rule } from "@/types";

const Card = styled.li`
  margin-bottom: 0.4rem;
  border: 1.5px solid var(--primary-color-dark);
  border-radius: 10px;
  background: #ffffff;
  transition: border-color 0.15s ease, background-color 0.15s ease;

  &:hover {
    border-color: var(--primary-color-xx-dark);
    background-color: var(--primary-color-extra-light);
  }
`;

const Row = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.5rem 0.75rem 0.75rem;
  cursor: pointer;
`;

const Identity = styled.div`
  flex: 1;
  min-width: 0;
  cursor: grab;
`;

const Code = styled.div`
  color: var(--primary-color-ultra-dark);
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.2;
`;

const Title = styled.div`
  overflow: hidden;
  color: #7a7a7a;
  font-size: 0.8rem;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const Stats = styled.div`
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.3rem;
`;

const ratingColor = (value?: number) => {
  if (!value) return null;
  if (value < 2) return "232, 173, 6";
  if (value < 3) return "84, 140, 243";
  return "85, 192, 147";
};

const Pill = styled.span<{ $rgb: string | null }>`
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: ${({ $rgb }) =>
    $rgb ? `rgba(${$rgb}, 0.14)` : "var(--background-grey)"};
  color: ${({ $rgb }) => ($rgb ? `rgb(${$rgb})` : "#acaeb5")};
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;

  small {
    font-size: 0.65rem;
    font-weight: 600;
    opacity: 0.8;
  }
`;

const Stat = ({
  label,
  name,
  value,
}: {
  label: string;
  name: string;
  value?: number;
}) => (
  <Pill
    $rgb={ratingColor(value)}
    title={`${name}${value ? `: ${value.toFixed(1)}` : " unknown"}`}
  >
    <small>{label}</small>
    {value ? value.toFixed(1) : "—"}
  </Pill>
);

const AddButton = styled.button<{ $used: boolean }>`
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: ${({ $used }) =>
    $used ? "var(--primary-color-light)" : "var(--primary-color-xx-dark)"};
  color: ${({ $used }) =>
    $used ? "var(--primary-color-xxx-dark)" : "#ffffff"};
  line-height: 1;
  cursor: ${({ $used }) => ($used ? "default" : "pointer")};
  transition: background-color 0.15s ease;

  &:hover {
    background: ${({ $used }) =>
      $used ? "var(--primary-color-light)" : "var(--primary-color-xxx-dark)"};
  }

  i {
    font-size: 0.75rem;
  }
`;

export const SkeletonCourse = () => (
  <Card>
    <Row>
      <Identity>
        <Code>
          <Skeleton width="5rem" />
        </Code>
        <Title>
          <Skeleton width="70%" />
        </Title>
      </Identity>
      <Skeleton width="5.5rem" height="1.4rem" borderRadius={999} />
    </Row>
  </Card>
);

interface CourseProps {
  course: CourseType;
  ruleId: Rule["id"] | null;
  onAdd: () => void;
  isUsed?: boolean;
}

export default function Course({
  course,
  ruleId,
  onAdd,
  isUsed = false,
}: CourseProps) {
  const [, drag, preview] = useDrag<DnDCourse, never, { isDragging: boolean }>(
    () => ({
      type: ItemTypes.COURSE_IN_SEARCH,
      item: { full_code: course.id, rule_id: ruleId == null ? -1 : ruleId },
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging(),
      }),
    }),
    [course]
  );
  useCourseDragPreview(preview);
  const code = course.id.replace(/-/g, " ");

  return (
    <Card>
      <ReviewPanelTrigger full_code={course.id} triggerType="click">
        <Row>
          <Identity ref={drag} className="draggable">
            <Code>{code}</Code>
            <Title title={course.title}>{course.title}</Title>
          </Identity>
          <Stats>
            <Stat
              label="Q"
              name="Course quality"
              value={course.course_quality}
            />
            <Stat label="D" name="Difficulty" value={course.difficulty} />
          </Stats>
          <AddButton
            type="button"
            $used={isUsed}
            aria-label={
              isUsed ? `${code} is already in your plan` : `Add ${code} to dock`
            }
            title={isUsed ? "Already in plan" : "Add to dock"}
            onClick={(e) => {
              e.stopPropagation();
              onAdd();
            }}
          >
            <i
              className={`fas ${isUsed ? "fa-check" : "fa-plus"}`}
              aria-hidden="true"
            />
          </AddButton>
        </Row>
      </ReviewPanelTrigger>
    </Card>
  );
}
