import React, { useState, useEffect } from "react";
import { Button } from "@radix-ui/themes";
import styled from "@emotion/styled";
import useSWR, { mutate } from "swr";
import Select from "react-select";
import {
  DegreeListing,
  DegreePlan,
  MajorOption,
  Options,
  SchoolOption,
} from "@/types";
import { postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { getLocalSemestersKey, interpolateSemesters } from "@/components/FourYearPlan/Semesters";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";

const PanelContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
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
`;

const CenteredFlexContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
`;

const ColumnsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  padding-top: 1%;
  padding-left: 5%;
  gap: 20px;
  min-height: 100%;

  @media (max-width: 768px) {
    flex-direction: column;
    padding-bottom: 5%;
  }
`;

export const Column = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 2rem;
  padding-right: 2%;
`;

const NextButtonContainer = styled.div`
  padding-top: 5%;
  padding-right: 15%;
  display: flex;
  flex-direction: row;
  justify-content: end;

  @media (max-width: 768px) {
    padding-right: 5%;
    width: 100%;
    justify-content: center;
  }
`;

const NextButton = styled(Button)`
  background-color: var(--primary-color-dark);
  @media (max-width: 768px) {
    width: 80%;
    margin: 0 auto;
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

export const schoolOptions = [
  { value: "BA", label: "Arts & Sciences" },
  { value: "BSE", label: "Engineering BSE" },
  { value: "BAS", label: "Engineering BAS" },
  { value: "BS", label: "Wharton" },
  { value: "BSN", label: "Nursing" }
];

const TextInput = styled.input`
  font-size: 1rem;
  padding: 2px 6px;
  width: 65%;
  height: 2.2rem;
  border-radius: 4px;
  border: 1px solid rgb(204, 204, 204);
`;

const FieldWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: left;
`;

const customSelectStylesLeft = {
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

const customSelectStylesRight = {
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

const OnboardingPage = ({
  setShowOnboardingModal,
  setActiveDegreeplan,
}: {
  setShowOnboardingModal: (arg0: boolean) => void;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
}) => {
  const [startingYear, setStartingYear] = useState<{ label: any, value: number } | null>(null);
  const [graduationYear, setGraduationYear] = useState<{ label: any, value: number } | null>(null);
  const [schools, setSchools] = useState<SchoolOption[]>([]);
  const [majors, setMajors] = useState<MajorOption[]>([]);
  const [minor, setMinor] = useState([]);
  const [name, setName] = useState("");

  const { create: createDegreeplan } = useSWRCrud<DegreePlan>(
    "/api/degree/degreeplans"
  );

  const complete = startingYear !== null &&
    graduationYear !== null &&
    schools.length > 0 &&
    majors.length > 0 &&
    name !== "";

  const { data: degrees, isLoading: isLoadingDegrees } =
    useSWR<DegreeListing[]>(`/api/degree/degrees`);

  const { data: options } = useSWR<Options>("/api/options");

  const getYearOptions = React.useCallback(() => {
    if (!options)
      return {
        startYears: [],
        gradYears: [],
      };
    const currentYear = Number(options.SEMESTER.substring(0, 4));
    return {
      // Up and down to 5 years
      startYears: [...Array(5).keys()].reverse().map((i) => ({
        value: currentYear - i,
        label: currentYear - i,
      })),
      gradYears: [...Array(5).keys()].map((i) => ({
        value: currentYear + i,
        label: currentYear + i,
      })),
    };
  }, [options]);

  const startingYearOptions = getYearOptions()?.startYears;
  const graduationYearOptions = getYearOptions()?.gradYears;

  const getMajorOptions = React.useCallback(() => {
    /** Filter major options based on selected schools/degrees */
    console.log(degrees);
    const majorOptions =
      degrees
        ?.filter((d) => schools.map((s) => s.value).includes(d.degree))
        .sort((d) => Math.abs((startingYear ? startingYear.value : d.year) - d.year))
        .map((degree) => ({
          value: degree,
          label: createMajorLabel(degree),
        }))
        .sort((a, b) => a.label.localeCompare(b.label));
    return majorOptions;
  }, [schools, startingYear]);

  const handleAddDegrees = () => {
    createDegreeplan({ name: name })
      .then((res) => {
        if (res) {
          if (startingYear && graduationYear) {
            const semesters = interpolateSemesters(startingYear.value, graduationYear.value);
            semesters[TRANSFER_CREDIT_SEMESTER_KEY] = [];
            window.localStorage.setItem(
              getLocalSemestersKey(res.id),
              JSON.stringify(semesters)
            );
          }
          setActiveDegreeplan(res);
          const updated = postFetcher(
            `/api/degree/degreeplans/${res.id}/degrees`,
            { degree_ids: majors.map((m) => m.value.id) }
          ); // add degree
          setActiveDegreeplan(res);
          setShowOnboardingModal(false);
        }
      });
  };

  return (
    <CenteredFlexContainer>
      <PanelContainer $maxWidth="90%" $minWidth="90%">
        <h1 style={{ paddingLeft: "5%", paddingTop: "5%" }}>
          Enter your degree(s):
        </h1>
        <ColumnsContainer>
          <Column>
            <FieldWrapper>
              <Label required>Degree Plan Name</Label>
              <TextInput
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder=""
              />
            </FieldWrapper>

            <FieldWrapper>
              <Label required>Starting Year</Label>
              <Select
                options={startingYearOptions}
                value={startingYear}
                onChange={(selectedOption) => setStartingYear(selectedOption)}
                isClearable
                placeholder="Select Year Started"
                styles={customSelectStylesLeft}
              />
            </FieldWrapper>

            <FieldWrapper>
              <Label required>Graduation Year</Label>
              <Select
                options={graduationYearOptions}
                value={graduationYear}
                onChange={(selectedOption) => setGraduationYear(selectedOption)}
                isClearable
                placeholder="Select Year of Graduation"
                styles={customSelectStylesLeft}
              />
            </FieldWrapper>
          </Column>

          <Column>
            <FieldWrapper>
              <Label required>School(s) or Program(s)</Label>
              <Select
                options={schoolOptions}
                value={schools}
                onChange={(selectedOptions) => setSchools([...selectedOptions])}
                isClearable
                isMulti
                placeholder="Select School or Program"
                styles={customSelectStylesRight}
                isLoading={isLoadingDegrees}
              />
            </FieldWrapper>

            <FieldWrapper>
              <Label required>Major(s)</Label>
              <Select
                options={getMajorOptions()}
                value={majors}
                onChange={(selectedOptions) => setMajors([...selectedOptions])}
                isClearable
                isMulti
                isDisabled={schools.length === 0}
                placeholder={
                  "Major - Concentration"
                }
                styles={customSelectStylesRight}
                isLoading={isLoadingDegrees}
              />
            </FieldWrapper>

            {/* <h5>Concentration</h5>
              <Select
                options={getConcentrationOptions()}
                value={concentrations}
                onChange={(selectedOption) => setConcentrations(selectedOption)}
                isClearable
                isMulti
                placeholder="Concentration"
                styles={customSelectStylesRight}
                isLoading={isLoadingDegrees}
              /> */}

            {/* <h5>Minor(s)</h5>
              <Select
                options={startingYearOptions}
                value={minor}
                onChange={(selectedOption) => setMinor(selectedOption)}
                isClearable
                isMulti
                placeholder="Minor Name"
                styles={customSelectStylesRight}
                isLoading={isLoadingDegreeplans}
              /> */}
            <NextButtonContainer>
              <NextButton
                onClick={handleAddDegrees}
                disabled={!complete}
                style={{
                  height: "35px",
                  width: "90px",
                  borderRadius: "7px",
                }}
              >
                Next
              </NextButton>
            </NextButtonContainer>
          </Column>
        </ColumnsContainer>
      </PanelContainer>
    </CenteredFlexContainer>
  );
};

export default OnboardingPage;
