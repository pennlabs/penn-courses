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

// One loop: the cursor drags a search result into a semester, and the course is counted for
// each requirement it can fill.
const cursorPath = keyframes`
  0% { left: 70%; top: 124px; opacity: 0; transform: scale(1); }
  6% { opacity: 1; }
  16% { left: 70%; top: 46px; transform: scale(1); }
  20% { left: 70%; top: 46px; transform: scale(0.85); }
  48% { left: 14%; top: 44px; transform: scale(0.85); }
  52% { left: 14%; top: 44px; transform: scale(1); }
  76% { left: 40%; top: 124px; opacity: 1; }
  86%, 100% { left: 40%; top: 124px; opacity: 0; }
`;

const chipPath = keyframes`
  0%, 20% { left: 62%; top: 36px; box-shadow: none; opacity: 1; }
  24% { box-shadow: 0 4px 10px rgba(30, 32, 60, 0.25); }
  48% { left: 8%; top: 34px; box-shadow: 0 4px 10px rgba(30, 32, 60, 0.25); }
  52%, 88% { left: 8%; top: 34px; box-shadow: none; opacity: 1; }
  96%, 100% { left: 8%; top: 34px; opacity: 0; }
`;

const ghostFade = keyframes`
  0%, 20% { opacity: 0; }
  24%, 88% { opacity: 1; }
  96%, 100% { opacity: 0; }
`;

const cardHighlight = keyframes`
  0%, 28% { border-color: var(--primary-color-dark); background: #ffffff; }
  34%, 50% { border-color: var(--modal-button-color); background: var(--primary-color-light); }
  54%, 100% { border-color: var(--primary-color-dark); background: #ffffff; }
`;

// Each requirement tag pops in a beat after the one before it.
const tagShow = (start: number) => keyframes`
  0%, ${start}% { opacity: 0; transform: scale(0.6); }
  ${start + 4}% { opacity: 1; transform: scale(1.08); }
  ${start + 7}%, 88% { opacity: 1; transform: scale(1); }
  96%, 100% { opacity: 0; transform: scale(1); }
`;

const Label = styled.div`
  position: absolute;
  left: 62%;
  top: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
`;

const StaticChip = styled.div`
  ${chipStyle}
`;

const Ghost = styled.div`
  ${chipStyle}
  left: 62%;
  top: 36px;
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
  top: 36px;
  z-index: 2;
  animation: ${chipPath} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    left: 8%;
    top: 34px;
    animation: none;
  }
`;

const Semester = styled.div`
  ${boxStyle}
  left: 4%;
  top: 6px;
  width: 52%;
  height: 128px;
  animation: ${cardHighlight} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const Tag = styled.div<{ $start: number }>`
  position: absolute;
  left: 8%;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
  background: #e3f4e8;
  color: #1e7a3c;
  font-size: 0.62rem;
  font-weight: 600;
  white-space: nowrap;
  transform-origin: left center;
  animation: ${(props) => tagShow(props.$start)} ${DURATION} ease-out infinite;
  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const Cursor = styled.i`
  ${cursorStyle}
  animation: ${cursorPath} ${DURATION} ease-in-out infinite;
`;

const REQUIREMENTS = [
  "CIS Major: Core",
  "Formal Reasoning",
  "Engineering Elective",
];

const SearchDragDemo = () => (
  <Stage aria-hidden>
    <Semester>
      <BoxTitle>Fall 2025</BoxTitle>
    </Semester>
    {REQUIREMENTS.map((title, i) => (
      <Tag key={title} $start={54 + i * 6} style={{ top: `${64 + i * 22}px` }}>
        <i className="fas fa-check" /> {title}
      </Tag>
    ))}
    <Label>Search results</Label>
    <Ghost>CIS 1200</Ghost>
    <StaticChip style={{ left: "62%", top: "66px" }}>CIS 1600</StaticChip>
    <StaticChip style={{ left: "62%", top: "96px" }}>CIS 1210</StaticChip>
    <Chip>CIS 1200</Chip>
    <Cursor className="fas fa-mouse-pointer" />
  </Stage>
);

export default SearchDragDemo;
