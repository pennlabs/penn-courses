import { keyframes } from "@emotion/react";
import styled from "@emotion/styled";
import React from "react";

import {
  BoxTitle,
  boxStyle,
  chipStyle,
  cursorStyle,
  DURATION,
  Stage,
} from "./demo";

// One loop: the cursor drags a course from a requirement into an empty semester card.
const cursorPath = keyframes`
  0% { left: 70%; top: 120px; opacity: 0; transform: scale(1); }
  6% { opacity: 1; }
  16% { left: 70%; top: 40px; transform: scale(1); }
  20% { left: 70%; top: 40px; transform: scale(0.85); }
  52% { left: 14%; top: 106px; transform: scale(0.85); }
  56% { left: 14%; top: 106px; transform: scale(1); }
  80% { left: 40%; top: 124px; opacity: 1; }
  90%, 100% { left: 40%; top: 124px; opacity: 0; }
`;

const chipPath = keyframes`
  0%, 20% { left: 62%; top: 30px; box-shadow: none; opacity: 1; }
  24% { box-shadow: 0 4px 10px rgba(30, 32, 60, 0.25); }
  52% { left: 8%; top: 96px; box-shadow: 0 4px 10px rgba(30, 32, 60, 0.25); }
  56%, 88% { left: 8%; top: 96px; box-shadow: none; opacity: 1; }
  96%, 100% { left: 8%; top: 96px; opacity: 0; }
`;

const ghostFade = keyframes`
  0%, 20% { opacity: 0; }
  24%, 88% { opacity: 1; }
  96%, 100% { opacity: 0; }
`;

const cardHighlight = keyframes`
  0%, 30% { border-color: var(--primary-color-dark); background: #ffffff; }
  36%, 54% { border-color: var(--modal-button-color); background: var(--primary-color-light); }
  58%, 100% { border-color: var(--primary-color-dark); background: #ffffff; }
`;

const Label = styled.div`
  position: absolute;
  left: 62%;
  top: 8px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
`;

const StaticChip = styled.div`
  ${chipStyle}
`;

// What stays behind in the requirement while the course is being dragged.
const Ghost = styled.div`
  ${chipStyle}
  left: 62%;
  top: 30px;
  border-style: dashed;
  color: transparent;
  background: none;
  animation: ${ghostFade} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    display: none;
  }
`;

const Chip = styled.div`
  ${chipStyle}
  left: 62%;
  top: 30px;
  z-index: 2;
  animation: ${chipPath} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    left: 8%;
    top: 96px;
    animation: none;
  }
`;

const Semester = styled.div`
  ${boxStyle}
  left: 4%;
  width: 50%;
  height: 60px;
`;

const TargetSemester = styled(Semester)`
  animation: ${cardHighlight} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const Cursor = styled.i`
  ${cursorStyle}
  animation: ${cursorPath} ${DURATION} ease-in-out infinite;
`;

const PlanDragDemo = () => (
  <Stage aria-hidden>
    <Label>Calculus</Label>
    <Ghost>MATH 1400</Ghost>
    <StaticChip style={{ left: "62%", top: "60px" }}>MATH 1070</StaticChip>
    <Semester style={{ top: "6px" }}>
      <BoxTitle>Fall 2025</BoxTitle>
    </Semester>
    <StaticChip style={{ left: "8%", top: "30px" }}>CIS 1200</StaticChip>
    <TargetSemester style={{ top: "72px" }}>
      <BoxTitle>Spring 2026</BoxTitle>
    </TargetSemester>
    <Chip>MATH 1400</Chip>
    <Cursor className="fas fa-mouse-pointer" />
  </Stage>
);

export default PlanDragDemo;
