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

// One loop: the cursor drags the course onto the requirement, confirms the override, and the
// requirement picks up its override badge.
const cursorPath = keyframes`
  0% { left: 30%; top: 100px; opacity: 0; transform: scale(1); }
  6% { opacity: 1; }
  16% { left: 12%; top: 26px; transform: scale(1); }
  20% { left: 12%; top: 26px; transform: scale(0.85); }
  48% { left: 58%; top: 44px; transform: scale(0.85); }
  52% { left: 58%; top: 44px; transform: scale(1); }
  64% { left: 64%; top: 104px; transform: scale(1); }
  68% { left: 64%; top: 104px; transform: scale(0.85); }
  72% { left: 64%; top: 104px; transform: scale(1); }
  86% { left: 84%; top: 118px; opacity: 1; }
  94%, 100% { left: 84%; top: 118px; opacity: 0; }
`;

const chipPath = keyframes`
  0%, 20% { left: 4%; top: 16px; box-shadow: none; opacity: 1; }
  24% { box-shadow: 0 4px 10px rgba(30, 32, 60, 0.25); }
  48% { left: 50%; top: 34px; box-shadow: 0 4px 10px rgba(30, 32, 60, 0.25); }
  52%, 88% { left: 50%; top: 34px; box-shadow: none; opacity: 1; }
  96%, 100% { left: 50%; top: 34px; opacity: 0; }
`;

const ghostFade = keyframes`
  0%, 20% { opacity: 0; }
  24%, 88% { opacity: 1; }
  96%, 100% { opacity: 0; }
`;

const requirementHighlight = keyframes`
  0%, 28% { border-color: var(--primary-color-dark); background: #ffffff; }
  34%, 52% { border-color: var(--modal-button-color); background: var(--primary-color-light); }
  56%, 100% { border-color: var(--primary-color-dark); background: #ffffff; }
`;

const popupShow = keyframes`
  0%, 52% { opacity: 0; transform: translateY(4px); }
  56%, 70% { opacity: 1; transform: translateY(0); }
  74%, 100% { opacity: 0; transform: translateY(0); }
`;

const badgeShow = keyframes`
  0%, 72% { opacity: 0; transform: scale(0.6); }
  76% { opacity: 1; transform: scale(1.1); }
  80%, 88% { opacity: 1; transform: scale(1); }
  96%, 100% { opacity: 0; transform: scale(1); }
`;

// What stays behind in the source column while the course is being dragged.
const Ghost = styled.div`
  ${chipStyle}
  left: 4%;
  top: 16px;
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
  left: 4%;
  top: 16px;
  z-index: 2;
  animation: ${chipPath} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    left: 50%;
    top: 34px;
    animation: none;
  }
`;

const Requirement = styled.div`
  ${boxStyle}
  left: 46%;
  top: 8px;
  width: 50%;
  height: 54px;
  animation: ${requirementHighlight} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const Badge = styled.span`
  font-size: 0.6rem;
  color: #b8860b;
  animation: ${badgeShow} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
`;

const Popup = styled.div`
  position: absolute;
  left: 22%;
  top: 76px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.45rem;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(30, 32, 60, 0.2);
  font-size: 0.68rem;
  color: var(--primary-color-ultra-dark);
  white-space: nowrap;
  animation: ${popupShow} ${DURATION} ease-in-out infinite;
  @media (prefers-reduced-motion: reduce) {
    display: none;
  }
`;

const PopupButton = styled.span`
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: var(--modal-button-color);
  color: #ffffff;
  font-weight: 500;
`;

const Cursor = styled.i`
  ${cursorStyle}
  animation: ${cursorPath} ${DURATION} ease-in-out infinite;
`;

const OverrideDemo = () => (
  <Stage aria-hidden>
    <Ghost>CIS 1200</Ghost>
    <Requirement>
      <BoxTitle>
        Writing Seminar
        <Badge>
          <i className="fas fa-star" /> override
        </Badge>
      </BoxTitle>
    </Requirement>
    <Chip>CIS 1200</Chip>
    <Popup>
      Count it anyway?
      <PopupButton>Override</PopupButton>
    </Popup>
    <Cursor className="fas fa-mouse-pointer" />
  </Stage>
);

export default OverrideDemo;
