import styled from "@emotion/styled";
import { HEADER_DEFAULT_BUFFER } from "./ReqPanel";
import { ProgramKind } from "./ProgramTabs";

const dropShadow = (props: { $isDroppable: boolean; $isOver: boolean }) => {
  if (!props.$isDroppable) return "none";
  const color = props.$isOver ? "--selected-color" : "--primary-color-dark";
  return `0px 0px 4px 2px var(${color})`;
};

export const RuleTitleWrapper = styled.div<{
  $headerHeight?: number;
  $zIndex?: number;
  $depth?: number;
  $kind?: ProgramKind | null;
}>`
  background-color: ${(props) =>
    props.$depth === 0 ? "var(--primary-color-dark)" : "var(--primary-color)"};
  ${(props) =>
    props.$depth === 0 && props.$kind
      ? `border-left: 3px solid var(--program-${props.$kind});`
      : ""}
  position: sticky;
  overflow: hidden; /* clips the progress fill to the rounded corners */
  margin-bottom: 0.5rem;
  border-radius: var(--req-item-radius);
  top: ${(props) => (props.$headerHeight || 0) + HEADER_DEFAULT_BUFFER}px;
  z-index: ${(props) => props.$zIndex || 995};
`;

export const ProgressBar = styled.div<{
  $progress: number;
  $animate?: boolean;
  $depth?: number;
}>`
  width: ${(props) => props.$progress * 100}%;
  transition: ${(props) => (props.$animate ? "width 300ms ease-out" : "none")};
  height: 100%;
  position: absolute;
  background-color: ${(props) =>
    props.$depth === 0
      ? "var(--primary-color-extra-dark)"
      : "var(--primary-color-dark)"};
`;

export const RuleTitle = styled.div<{ $depth?: number }>`
  position: relative;
  font-size: 1rem;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  color: ${(props) =>
    props.$depth === 0
      ? "var(--primary-color-ultra-dark)"
      : "var(--text-color)"};
  padding: 0.5rem 1.25rem;
`;

/** A top-level rule stacks its percentage under its name; deeper rules keep them on one line. */
export const RuleTitleText = styled.div<{ $stacked: boolean }>`
  ${(props) =>
    props.$stacked
      ? `
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.05rem;
    line-height: 1.3;

    > span {
      margin-left: 0;
      font-size: inherit;
    }
  `
      : ""}
`;

export const RuleLeafWrapper = styled.div<{
  $isDroppable: boolean;
  $isOver: boolean;
}>`
  padding: 0.5rem 0.5rem 0.5rem 0rem;
  margin-left: 0;
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
  box-shadow: ${dropShadow};
  transition: box-shadow 150ms ease-out;
`;

/** The title, satisfied check and progress of a requirement, on one line above its courses. */
export const LeafProgress = styled.span`
  font-size: 0.9rem;
  font-weight: 600;
  color: #5a5a5a;
  white-space: nowrap;

  small {
    margin-left: 0.2em;
    font-size: 0.75rem;
    font-weight: 500;
  }
`;

export const LeafStatus = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-shrink: 0;
`;

export const CusCourses = styled.div`
  font-weight: 500;
  font-size: 0.9rem;
  white-space: nowrap;

  sup {
    margin-right: 0.2em;
  }

  sub {
    margin-left: 0.2em;
  }
`;

export const Row = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

export const Indented = styled.div<{ $depth: number }>`
  /* Only the first level draws a guide; deeper ones would use up a narrow column. */
  ${(props) =>
    props.$depth === 0
      ? `
    margin-left: 1.25rem;
    padding-left: 0.65rem;
    border-left: 2px solid var(--primary-color-dark);
  `
      : "margin-left: 0.5rem;"}
  margin-bottom: 0.5rem;
`;

export const Column = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0rem;
`;

export const PickNWrapper = styled.div`
  background-color: var(--primary-color-extra-light);
  padding: 0.5rem;
  padding-bottom: 0.25rem;
  border-radius: 0.5rem;
`;

export const PickNTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  font-size: 0.95rem;
  color: #3a3a3a;
  margin-bottom: 0.5rem;
  margin-left: 0.25rem;
`;

export const RuleLeafLabel = styled.div`
  font-size: 0.95rem;
  font-weight: 600;
  color: #3a3a3a;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
`;

export const RuleLeafTitle = styled.span`
  min-width: 0;
  font-weight: 700;
  letter-spacing: -0.01em;
`;

export const OverrideTagWrapper = styled.div`
  position: relative;
  display: inline-flex;
`;

export const OverrideTag = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font: inherit;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
  background: var(--primary-color-light);
  border: 1px solid var(--primary-color-dark);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;

  i {
    color: var(--primary-color-xxx-dark);
  }

  &:hover,
  &[aria-expanded="true"] {
    background: var(--primary-color);
    border-color: var(--primary-color-xx-dark);
  }
`;

export const OverridePopover = styled.div`
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 1000;
  min-width: 210px;
  padding: 0.6rem 0.5rem 0.4rem;
  border: 1px solid var(--primary-color-dark);
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(61, 65, 119, 0.14);
  font-size: 0.8rem;
`;

export const OverridePopoverTitle = styled.div`
  margin: 0 0.35rem 0.35rem;
  color: var(--primary-color-xxx-dark);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
`;

export const OverrideItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0.35rem;
  border-radius: 8px;

  &:hover {
    background: var(--primary-color-extra-light);
  }
`;

export const OverrideItemName = styled.span`
  color: var(--primary-color-ultra-dark);
  font-weight: 600;
`;

export const RemoveOverrideButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: none;
  color: var(--primary-color-xxx-dark);
  font-size: 0.75rem;
  cursor: pointer;

  &:hover {
    background: var(--primary-color-light);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Override modal styles
export const OverrideModalOverlay = styled.div`
  position: fixed;
  inset: 0;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(61, 65, 119, 0.35);
`;

export const OverrideModalCard = styled.div`
  width: 90%;
  max-width: 400px;
  padding: 1.5rem;
  border: 1px solid var(--primary-color-dark);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 12px 32px rgba(61, 65, 119, 0.2);
`;

export const OverrideModalTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.9rem;
  color: var(--primary-color-ultra-dark);
  font-size: 1.1rem;
  font-weight: 700;
`;

export const OverrideModalIcon = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: var(--primary-color-light);
  color: var(--primary-color-xxx-dark);
  font-size: 0.85rem;
`;

export const OverrideModalBody = styled.div`
  margin-bottom: 1.25rem;
  color: var(--modal-text-color);
  font-size: 0.9rem;
  line-height: 1.55;

  p {
    margin: 0 0 0.6rem;
  }
`;

export const OverrideModalNote = styled.p`
  padding: 0.5rem 0.7rem;
  border-radius: 8px;
  background: var(--primary-color-extra-light);
  color: var(--primary-color-ultra-dark);
  font-size: 0.82rem;
`;

export const OverrideModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
`;

export const OverrideModalButton = styled.button<{ $primary?: boolean }>`
  padding: 0.45rem 1.1rem;
  border: none;
  border-radius: 8px;
  background: ${(props) =>
    props.$primary ? "var(--primary-color-xx-dark)" : "transparent"};
  color: ${(props) =>
    props.$primary ? "#ffffff" : "var(--primary-color-xxx-dark)"};
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;

  &:hover {
    background: ${(props) =>
      props.$primary
        ? "var(--primary-color-xxx-dark)"
        : "var(--primary-color-light)"};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

export const OverrideCourseName = styled.strong`
  color: var(--primary-color-ultra-dark);
`;

export const RuleLeafContainer = styled.div<{
  $isDroppable: boolean;
  $isOver: boolean;
}>`
  display: flex;
  flex-direction: column;
  margin-top: 0.25rem;
  padding: 0.5rem 0.5rem 0;
  border-radius: 8px;
  box-shadow: ${dropShadow};
  transition: box-shadow 150ms ease-out;
`;

/** Marks a requirement the student is waived from, e.g. by an AP exam, with a control to undo it. */
export const WaivedTag = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
  background: var(--primary-color);
  border: 1px solid var(--primary-color-dark);
  border-radius: 4px;
  padding: 0.1rem 0.15rem 0.1rem 0.4rem;
  white-space: nowrap;
`;

export const RemoveWaiverButton = styled.button`
  display: inline-flex;
  align-items: center;
  background: none;
  border: none;
  color: var(--primary-color-xxx-dark);
  font-size: 0.65rem;
  padding: 0.1rem 0.25rem;
  border-radius: 3px;
  cursor: pointer;

  &:hover {
    background: var(--primary-color-dark);
  }
`;

/**
 * Waives a requirement. Shown while its requirement is hovered (always on touch screens), so the
 * panel isn't covered in buttons.
 */
export const WaiveButton = styled.button`
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-xxx-dark);
  background: transparent;
  border: 1px dashed var(--primary-color-extra-dark);
  border-radius: 4px;
  padding: 0.1rem 0.4rem;
  white-space: nowrap;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease;

  .rule-leaf:hover &,
  &:focus-visible {
    opacity: 1;
  }

  @media (hover: none) {
    opacity: 1;
  }

  &:hover {
    background: var(--primary-color-light);
    border-style: solid;
  }
`;
