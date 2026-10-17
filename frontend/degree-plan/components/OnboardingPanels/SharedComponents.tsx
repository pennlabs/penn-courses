import styled from "@emotion/styled";
import { Button } from "@radix-ui/themes";

// The white card each onboarding step sits in (WelcomeLayout, CreateWithTranscriptPanel).
export const panelCard = `
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
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
  color: darkred;
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
  border-radius: 7px;
  transition: all 0.25s;
  background-color: ${({ disabled }) =>
    disabled ? "var(--primary-color-dark)" : "#0000ff"};
  color: ${({ disabled }) => (disabled ? "var(--gray-a8)" : "white")};

  @media (max-width: 768px) {
    width: 80%;
    margin: 0 auto;
  }
`;

export const Upload = styled.div`
  width: 350px;
  height: 100px;
  border: 1px dashed #808080;
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  transition: all 0.25s;
  &:hover {
    background-color: #f6f6f6;
  }
`;

export const TextButton = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
  width: fit-content;
  border-bottom: 1px solid #aaaaaa00;
  &:hover {
    // text-decoration: underline;
    border-bottom: 1px solid #aaa;
    cursor: pointer;
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
