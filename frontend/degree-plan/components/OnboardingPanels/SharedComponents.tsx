import styled from "@emotion/styled";
import { Button } from "@radix-ui/themes";

export const PanelContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
  border-radius: 10px;
  box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
  background-color: #ffffff;
  margin: 1rem;
  min-height: 85%;
  // overflow: hidden; /* Hide scrollbars */
  width: ${(props) => (props.$maxWidth || props.$maxWidth ? "auto" : "100%")};
  max-width: ${(props) => (props.$maxWidth ? props.$maxWidth : "auto")};
  min-width: ${(props) => (props.$minWidth ? props.$minWidth : "auto")};
  position: relative;
  padding-bottom: "5%";
  z-index: 100000;
`;

export const ChooseContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
  padding-top: 5%;
  border-radius: 10px;
  box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
  background-color: #ffffff;
  margin: 1rem;
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

export const CenteredFlexContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
`;

export const ColumnsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  padding-top: 1%;
  padding-left: 5%;
  padding-right: 5%;
  gap: 20px;
  min-height: 100%;
  padding-bottom: 5%;

  @media (max-width: 768px) {
    flex-direction: column;
    padding-bottom: 5%;
  }
`;

export const CourseContainer = styled.div`
  max-height: 48vh;
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
  padding-right: 2%;
  padding-bottom: 2rem;

  // Scroll shadow credits: https://css-tricks.com/books/greatest-css-tricks/scroll-shadows/
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overflow-scrolling: touch;

  background:
    /* Shadow Cover TOP */
    linear-gradient(
      white 30%,
      rgba(255, 255, 255, 0)
    ) center top,
    
    /* Shadow Cover BOTTOM */
    linear-gradient(
      rgba(255, 255, 255, 0), 
      white 70%
    ) center bottom,
    
    /* Shadow TOP */
    radial-gradient(
      farthest-side at 50% 0,
      rgba(0, 0, 0, 0.4),
      rgba(0, 0, 0, 0)
    ) center top,
    
    /* Shadow BOTTOM */
    radial-gradient(
      farthest-side at 50% 100%,
      rgba(0, 0, 0, 0.3),
      rgba(0, 0, 0, 0)
    ) center bottom;
  
  background-repeat: no-repeat;
  background-size: 100% 40px, 100% 40px, 100% 14px, 100% 14px;
  background-attachment: local, local, scroll, scroll;
}
`;

export const Column = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
`;

export const NextButtonContainer = styled.div`
  padding-top: 5%;
  // padding-right: 15%;
  display: flex;
  flex-direction: row;
  justify-content: end;

  @media (max-width: 768px) {
    padding-right: 5%;
    width: 100%;
    justify-content: center;
  }
`;

export const NextButton = styled(Button)<{ disabled: boolean }>`
  background-color: ${({ disabled }) =>
    disabled ? "var(--primary-color-dark)" : "#0000ff"};

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

export const Label = styled.h5<{ required: boolean }>`
  padding-top: 3%;
  font-size: 1rem;
  &:after {
    content: "*";
    color: red;
    display: ${({ required }) => (required ? "inline" : "none")};
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

export const FieldWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: left;
`;

export const TextInput = styled.input`
  font-size: 1rem;
  padding: 2px 6px;
  width: 65%;
  height: 2.2rem;
  border-radius: 4px;
  border: 1px solid rgb(204, 204, 204);
`;

export const customSelectStylesLeft = {
  control: (provided: any) => ({
    ...provided,
    width: 250,
    minHeight: "35px",
    height: "35px",
  }),
  menu: (provided: any) => ({
    ...provided,
    width: 250,
    maxHeight: 200,
  }),
  valueContainer: (provided: any) => ({
    ...provided,
    height: "35px",
    padding: "0 6px",
  }),
  input: (provided: any) => ({
    ...provided,
    margin: "0px",
  }),
  indicatorsContainer: (provided: any) => ({
    ...provided,
    height: "35px",
  }),
};

export const customSelectStylesRight = {
  control: (provided: any) => ({
    ...provided,
    width: "80%",
    minHeight: "35px",
    height: "35px",
  }),
  menu: (provided: any) => ({
    ...provided,
    width: 500,
    maxHeight: "85rem",
  }),
  valueContainer: (provided: any) => ({
    ...provided,
    height: "35px",
    padding: "0 6px",
  }),
  input: (provided: any) => ({
    ...provided,
    margin: "0px",
  }),
  indicatorsContainer: (provided: any) => ({
    ...provided,
    height: "35px",
  }),
  multiValue: (provided: any) => ({
    ...provided,
    borderRadius: "8px",
    maxWidth: "200px",
  }),
  multiValueLabel: (provided: any) => ({
    ...provided,
    borderRadius: "8px",
    // maxWidth: "90px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  loadingIndicator: (provided: any) => ({
    ...provided,
    color: "gray",
  }),
};

export const customSelectStylesCourses = {
  control: (provided: any) => ({
    ...provided,
    width: "100%",
    minHeight: "35px",
    zIndex: -1,
  }),
  menu: (provided: any) => ({
    ...provided,
    width: 500,
    maxHeight: "85rem",
  }),
  valueContainer: (provided: any) => ({
    ...provided,
    zIndex: -1,
  }),
  input: (provided: any) => ({
    ...provided,
    margin: "0px",
  }),
  indicatorsContainer: (provided: any) => ({
    ...provided,
    display: "none",
  }),
  multiValue: (provided: any) => ({
    ...provided,
    borderRadius: "8px",
    maxWidth: "200px",
    paddingRight: 4,
    marginRight: 3,
  }),
  multiValueLabel: (provided: any) => ({
    ...provided,
    borderRadius: "8px",
    maxWidth: "90px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  loadingIndicator: (provided: any) => ({
    ...provided,
    color: "gray",
  }),
};


export const schoolOptions = [
  { value: "BA", label: "Arts & Sciences" },
  { value: "BSE", label: "Engineering BSE" },
  { value: "BAS", label: "Engineering BAS" },
  { value: "BS", label: "Wharton" },
  { value: "BSN", label: "Nursing" },
  { value: "MSE", label: "Engineering AM" },
];