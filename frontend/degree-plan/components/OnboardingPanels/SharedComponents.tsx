import styled from "@emotion/styled";
import { Button } from "@radix-ui/themes";

// The white card each onboarding step sits in (WelcomeLayout, CreateWithTranscriptPanel).
export const panelCard = `
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: var(--panel-shadow);
  margin: 1rem;
`;

export const ChooseContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
  ${panelCard}
  padding-top: 5%;
  min-height: 85%;
  overflow: hidden; /* Hide scrollbars */
  width: ${(props) => (props.$maxWidth || props.$maxWidth ? "auto" : "100%")};
  max-width: ${(props) => (props.$maxWidth ? props.$maxWidth : "auto")};
  min-width: ${(props) => (props.$minWidth ? props.$minWidth : "auto")};
  position: relative;
  padding-bottom: "5%";
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
`;

export const ContainerGroup = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
`;

export const ErrorText = styled.p`
  color: var(--error-color);
  min-height: 17px;
`;

export const PrivacyNote = styled.p`
  color: #777777;
  font-size: 0.85rem;
  line-height: 1.4;
  max-width: 350px;
  text-align: center;
`;

export const CenteredFlexContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
`;

export const NextButton = styled(Button)<{ disabled: boolean }>`
  height: 45px;
  width: 100px;
  border-radius: 8px;
  font-weight: 700;
  transition: background-color 0.15s;
  background-color: ${({ disabled }) =>
    disabled ? "var(--primary-color-dark)" : "var(--primary-color-xx-dark)"};
  color: ${({ disabled }) => (disabled ? "var(--gray-a8)" : "white")};

  &:hover:not(:disabled) {
    background-color: var(--primary-color-xxx-dark);
  }

  @media (max-width: 768px) {
    width: 80%;
    margin: 0 auto;
  }
`;

export const Upload = styled.div`
  width: 350px;
  height: 100px;
  border: 1.5px dashed var(--primary-color-extra-dark);
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  color: var(--primary-color-xxx-dark);
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
  &:hover {
    border-color: var(--primary-color-xxx-dark);
    background-color: var(--primary-color-light);
  }
`;

export const TextButton = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
  width: fit-content;
  color: var(--primary-color-xxx-dark);
  font-weight: 500;
  border-bottom: 1px solid transparent;
  cursor: pointer;
  &:hover {
    color: var(--primary-color-ultra-dark);
    border-bottom-color: currentColor;
  }
`;

export const schoolOptions = [
  { value: "BA", label: "Arts & Sciences" },
  { value: "BSE", label: "Engineering BSE" },
  { value: "BAS", label: "Engineering BAS" },
  { value: "BS", label: "Wharton" },
  { value: "BSN", label: "Nursing" },
  { value: "MSE", label: "Engineering MSE" },
];
