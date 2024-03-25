import React, { useState, useEffect } from "react";
import { Button } from "@radix-ui/themes";
import { PlusIcon } from "@radix-ui/react-icons";
import { Theme } from "@radix-ui/themes";
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

export const Label = styled.h5`
  padding-top: 3%;
  font-size: 1rem;
  &:after {
    content: "*";
    color: red;
    display: ${({ required }) => (required ? "inline" : "none")};
  }
`;

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
  control: (provided) => ({
    ...provided,
    width: 250,
    minHeight: "35px",
    height: "35px",
  }),
  menu: (provided) => ({
    ...provided,
    width: 250,
    maxHeight: 200,
  }),
  valueContainer: (provided) => ({
    ...provided,
    height: "35px",
    padding: "0 6px",
  }),
  input: (provided) => ({
    ...provided,
    margin: "0px",
  }),
  indicatorsContainer: (provided) => ({
    ...provided,
    height: "35px",
  }),
};

const customSelectStylesRight = {
  control: (provided) => ({
    ...provided,
    width: "80%",
    minHeight: "35px",
    height: "35px",
  }),
  menu: (provided) => ({
    ...provided,
    width: 500,
    maxHeight: "85rem",
  }),
  valueContainer: (provided) => ({
    ...provided,
    height: "35px",
    padding: "0 6px",
  }),
  input: (provided) => ({
    ...provided,
    margin: "0px",
  }),
  indicatorsContainer: (provided) => ({
    ...provided,
    height: "35px",
  }),
  multiValue: (provided) => ({
    ...provided,
    borderRadius: "8px",
    maxWidth: "200px",
  }),
  multiValueLabel: (provided) => ({
    ...provided,
    borderRadius: "8px",
    maxWidth: "90px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  loadingIndicator: (provided) => ({
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
  const [startingYear, setStartingYear] = useState(null);
  const [graduationYear, setGraduationYear] = useState(null);
  const [schools, setSchools] = useState<SchoolOption[]>([]);
  const [majors, setMajors] = useState<MajorOption[]>([]);
  const [concentrations, setConcentrations] = useState([]);
  const [minor, setMinor] = useState([]);
  const [complete, setComplete] = useState(false);
  const [name, setName] = useState("");

  const { create: createDegreeplan } = useSWRCrud<DegreePlan>(
    "/api/degree/degreeplans"
  );

  useEffect(() => {
    setComplete(
      startingYear !== null &&
        graduationYear !== null &&
        schools.length > 0 &&
        majors.length > 0 &&
        name !== ""
    );
  }, [startingYear, graduationYear, schools, majors, name]);

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
      startYears: [...Array(5).keys()].map((i) => ({
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

  const defaultSchools = ["BA", "BSE", "BAS", "BS", "BSN"];

  const schoolOptions = defaultSchools.map((d) => ({
    value: d,
    label: d,
  }));

  /** Create label for major listings */
  const createMajorLabel = (degree: DegreeListing) => {
    const concentration =
      degree.concentration && degree.concentration !== "NONE"
        ? ` - ${degree.concentration}`
        : "";
    return `${degree.major}${concentration}`;
  };

  const getMajorOptions = React.useCallback(() => {
    /** Filter major options based on selected schools/degrees */
    const majorOptions =
      degrees
        ?.filter((d) => schools.map((s) => s.value).includes(d.degree))
        .map((degree) => ({
          value: degree,
          label: createMajorLabel(degree),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [];
    return majorOptions;
  }, [schools]);

  // const getConcentrationOptions = React.useCallback(() => {
  //   /** Filter concentration options based on selected majors */
  //   const concentrationOptions = degrees
  //     ?.filter(d => majors.map(s => s.value).includes(d.major))
  //     .map((degree) => ({ value: degree.concentration, label: degree.concentration}))
  //     || [];
  //     console.log(concentrationOptions)
  //   return concentrationOptions;
  // }, [majors]);

  // TODO: Load in minorOptions

  const handleAddDegrees = () => {
    createDegreeplan({ name: name })
      .catch((e) => alert("Trouble adding degrees: " + e))
      .then((res) => {
        if (res) {
          setActiveDegreeplan(res);
          const updated = postFetcher(
            `/api/degree/degreeplans/${res.id}/degrees`,
            { degree_ids: majors.map((m) => m.value.id) }
          ); // add degree
          // mutate(`api/degree/degreeplans/${res.id}`, updated, { populateCache: true, revalidate: false }) // use updated degree plan returned
          // mutate(key => key && key.startsWith(`/api/degree/degreeplans/${res.id}/fulfillments`)) // refetch the fulfillments
          setActiveDegreeplan(res);
          localStorage.setItem(
            "PDP-start-grad-years",
            JSON.stringify({
              startingYear: startingYear?.value,
              graduationYear: graduationYear?.value,
            })
          );
          // TODO: update the backend on user's start/grad years
          setShowOnboardingModal(false);
        }
      });
  };

  return (
    <CenteredFlexContainer>
      <PanelContainer $maxWidth="90%" $minWidth="90%">
        <h1 style={{ paddingLeft: "5%", paddingTop: "5%" }}>
          Degree Information
        </h1>
        <ColumnsContainer>
          <Column>
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

            <FieldWrapper>
              <Label required>Degree Plan Name</Label>
              <TextInput
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder=""
              />
            </FieldWrapper>
          </Column>

          <Column>
            <FieldWrapper>
              <Label required>School(s) or Program(s)</Label>
              <Select
                options={schoolOptions}
                value={schools}
                onChange={(selectedOption) => setSchools(selectedOption)}
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
                onChange={(selectedOption) => setMajors(selectedOption)}
                isClearable
                isMulti
                placeholder={
                  schools.length > 0
                    ? "Major - Concentration"
                    : "Please Select Program First"
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
