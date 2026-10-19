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
