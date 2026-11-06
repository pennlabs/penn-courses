import styled from "@emotion/styled";
import { CenteredFlexContainer, panelCard } from "./SharedComponents";
import { color } from "./onboardingStyles";

export const Page = styled(CenteredFlexContainer)`
  overflow: hidden;
  color: ${color.text};
`;

const contentMaxWidth = 1200;
const contentWidth = `
  width: 100%;
  max-width: ${contentMaxWidth}px;
  margin: 0 auto;
  box-sizing: border-box;
`;

export const Card = styled.div`
  ${panelCard}
  width: 90%;
  height: 85%;
  overflow: hidden;
  box-sizing: border-box;
  border: 1px solid ${color.border};
  display: flex;
  flex-direction: column;
`;

export const ScrollArea = styled.div`
  flex: 1;
  position: relative;
`;

export const ScrollContent = styled.div`
  position: absolute;
  inset: 0;
  overflow-y: auto;
`;

export const Header = styled.div`
  ${contentWidth}
  padding: 32px 40px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;

  @media (max-width: 600px) {
    padding: 24px 16px 0;
  }
`;

export const Title = styled.h1`
  margin: 0;
  color: ${color.heading};
  font-size: 32px;
  line-height: 1.15;
  font-weight: 700;
`;

export const Body = styled.div`
  ${contentWidth}
  display: flex;
  flex-direction: column;
  gap: 36px;
  padding: 32px 40px 40px;

  @media (max-width: 600px) {
    padding: 24px 16px 32px;
  }
`;

export const Section = styled.section`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

export const TextInput = styled.input`
  height: 44px;
  padding: 0 14px;
  border: 1px solid ${color.inputBorder};
  border-radius: 8px;
  font: inherit;
  font-size: 15px;
  color: ${color.text};
  background: #ffffff;
  box-sizing: border-box;
  width: 100%;

  &::placeholder {
    color: ${color.subtle};
  }

  &:focus {
    outline: none;
    border-color: ${color.accent};
    box-shadow: ${color.focusRing};
  }
`;

export const FieldError = styled.p`
  margin: 0;
  font-size: 13px;
  color: ${color.required};
`;

export const Footer = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  // Divider spans the card; the button lines up with the capped content above.
  padding: 20px max(40px, calc((100% - ${contentMaxWidth}px) / 2 + 40px));
  border-top: 1px solid ${color.border};
  background: #fcfcfd;
  border-radius: 0 0 10px 10px;

  @media (max-width: 600px) {
    padding: 16px;
  }
`;
