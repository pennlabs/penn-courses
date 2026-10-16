import { css } from "styled-components";

/* Certain style patterns used to be copy-pasted everywhere. This file consolidates them into reusable blocks */

export const interactiveTransition = css`
  transition: background-color ${({ theme }) => theme.motion.duration.fast}
      ${({ theme }) => theme.motion.ease.standard},
    color ${({ theme }) => theme.motion.duration.fast}
      ${({ theme }) => theme.motion.ease.standard},
    border-color ${({ theme }) => theme.motion.duration.fast}
      ${({ theme }) => theme.motion.ease.standard};
`;

export const pill = css<{ $isSelected?: boolean }>`
  display: flex;
  align-items: center;
  height: ${({ theme }) => theme.size.controlHeight};
  padding: 6px 11px;
  border-radius: ${({ theme }) => theme.radius.md};
  font-family: ${({ theme }) => theme.font.family.sans};
  font-size: ${({ theme }) => theme.font.size.md};
  cursor: pointer;
  ${interactiveTransition}
  background: ${({ theme, $isSelected }) =>
    $isSelected ? theme.color.surface.selected : theme.color.surface.page};
  color: ${({ theme, $isSelected }) =>
    $isSelected ? theme.color.text.inverse : theme.color.text.primary};

  &:hover {
    background: ${({ theme, $isSelected }) =>
      $isSelected
        ? theme.color.surface.selectedHover
        : theme.color.surface.hover};
  }
`;

// Floating panel shared by SelectBox's search list and CustomDropdown
export const dropdownSurface = css`
  position: absolute;
  top: 0;
  left: 0;
  z-index: ${({ theme }) => theme.zIndex.dropdown};
  border-radius: ${({ theme }) => theme.radius.md};
  background: ${({ theme }) => theme.color.surface.page};
  box-shadow: ${({ theme }) => theme.shadow.dropdown};
`;

// Bordered white card used by the results panel and the filter sidebar
export const card = css`
  display: flex;
  flex-direction: column;
  padding: 12px;
  border-radius: ${({ theme }) => theme.radius.lg};
  background: ${({ theme }) => theme.color.surface.card};
  border: 1px solid ${({ theme }) => theme.color.border.default};
`;

// Shared by Header's plain <a> and its react-router <Link> 
export const linkStyles = css`
  text-decoration: none;
  color: ${({ theme }) => theme.color.text.primary};
  font-size: ${({ theme }) => theme.font.size.xl};
  ${interactiveTransition}

  &:hover {
    color: ${({ theme }) => theme.color.text.black};
    text-decoration: none;
  }
`;

export const unstyledButton = css`
  all: unset;
  box-sizing: border-box;
  cursor: pointer;
  font-family: ${({ theme }) => theme.font.family.sans};
`;

export const errorField = css`
  color: ${({ theme }) => theme.color.feedback.errorFg};
  background: ${({ theme }) => theme.color.feedback.errorBg};
  border: 1px solid ${({ theme }) => theme.color.feedback.errorBorder};
`;
