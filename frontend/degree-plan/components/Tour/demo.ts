import styled from "@emotion/styled";

// Shared pieces of the tour's looping drag-and-drop illustrations.
export const DURATION = "6s";

export const Stage = styled.div`
  position: relative;
  height: 140px;
  margin: 0.25rem 0 0.9rem;
  border-radius: 8px;
  background: var(--primary-color-light);
  overflow: hidden;
  user-select: none;
`;

export const chipStyle = `
  position: absolute;
  padding: 0.2rem 0.5rem;
  border: 1px solid var(--primary-color-dark);
  border-radius: 6px;
  background: #ffffff;
  color: var(--primary-color-ultra-dark);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
`;

export const boxStyle = `
  position: absolute;
  box-sizing: border-box;
  padding: 0.3rem 0.45rem;
  border: 1px solid var(--primary-color-dark);
  border-radius: 6px;
  background: #ffffff;
`;

export const BoxTitle = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
`;

export const cursorStyle = `
  position: absolute;
  z-index: 3;
  font-size: 1rem;
  color: var(--primary-color-ultra-dark);
  transform-origin: top left;
  @media (prefers-reduced-motion: reduce) {
    display: none;
  }
`;
