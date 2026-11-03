import styled from "@emotion/styled";
import { GrayIcon, Icon } from "@/components/common/bulma_derived_components";

const COURSE_BORDER_RADIUS = "9px";

const HIGHLIGHT_VARIANT_COLORS = {
  selected: "#E6F4EA",
  unselected: "var(--warning-bg)",
} as const;

export const Exclamation = styled(Icon)<{ $color: string }>`
  width: 1rem;
  height: 1rem;
  display: flex;
  fill: ${(props) => props.$color};
`;

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

export const CloseIcon = styled(GrayIcon)<{ $hidden: boolean }>`
  visibility: ${(props) => (props.$hidden ? "hidden" : "visible")};
  cursor: pointer;
`;

export const CourseBadge = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.25rem;
`;

export const IconBadge = styled.div`
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

export const InfoIconButton = styled.button`
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

export const InfoPopoverWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

export const InfoPopover = styled.div`
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

export const PopoverSection = styled.div`
  overflow: visible;

  &:not(:last-child) {
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #eee;
  }
`;

export const PopoverLabel = styled.div`
  font-weight: 600;
  font-size: 0.7rem;
  color: #888;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
`;

export const RuleList = styled.ul`
  margin: 0;
  padding-left: 1rem;
  list-style-position: outside;

  li {
    margin-bottom: 0.15rem;
    padding-left: 0.15rem;
  }
`;

export const OverrideBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.7rem;
  color: var(--warning-text);
  font-weight: 600;
`;

// A Gmail-style status dot: the course's level at a glance, and the handle for changing it.
export const LevelDot = styled.span<{ $color: string | null }>`
  display: inline-block;
  width: 0.6rem;
  height: 0.6rem;
  flex-shrink: 0;
  border-radius: 50%;
  box-sizing: border-box;
  background: ${({ $color }) => $color ?? "transparent"};
  border: 2px solid ${({ $color }) => $color ?? "#b5b5b5"};
`;

export const LevelDotButton = styled.button`
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

export const LevelMenu = styled.div`
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

export const LevelMenuHeading = styled.div`
  padding: 0.3rem 0.9rem 0.4rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.03em;
`;

export const LevelMenuItem = styled.button<{ $active: boolean }>`
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

export const LevelMenuLabel = styled.span`
  flex-grow: 1;
`;

export const LevelMenuCheck = styled.i`
  font-size: 0.75rem;
  color: #555;
`;

export const LevelMenuError = styled.div`
  padding: 0.3rem 0.9rem 0.4rem;
  font-size: 0.8rem;
  color: var(--error-color);
  white-space: normal;
`;

export const SwitchRuleButton = styled.button`
  border: 1px solid #d7cc86;
  border-radius: 6px;
  background: var(--warning-bg);
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

export const DisplacedBanner = styled.div`
  margin-top: 0.4rem;
  padding: 0.35rem 0.55rem;
  border-radius: 6px;
  background: #fff3e0;
  border: 1px solid #e0c080;
  color: #7a4f00;
  font-size: 0.78rem;
  line-height: 1.35;
`;
