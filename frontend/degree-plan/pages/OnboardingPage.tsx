import React, { useState, useEffect } from "react";
import { Button } from "@radix-ui/themes";
import { PlusIcon } from "@radix-ui/react-icons";
import { Theme } from "@radix-ui/themes";
import { PanelContainer } from "./FourYearPlanPage";
import styled from "@emotion/styled";
import useSWR from "swr";
import Select from "react-select";

const CenteredFlexContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
`;

const ColumnsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  padding-top: 10px;
  padding-left: 100px;
  gap: 20px;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const Column = styled.div`
  flex: 1;
  gap: 10px;
  padding-right: 20px;
  h5 {
    padding-top: 25px;
  }
`;

const NextButton = styled(Button)`
  position: absolute;
  bottom: 60px;
  right: 100px;
`;

const Label = styled.h5`
  padding-top: 25px;
  &:after {
    content: "*";
    color: red;
    display: ${({ required }) => (required ? "inline" : "none")};
  }
`;

const customSelectStylesLeft = {
  control: (provided) => ({
    ...provided,
    width: 250,
    minHeight: "35px",
    height: "35px",
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
    width: 500,
    minHeight: "35px",
    height: "35px",
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
};

const OnboardingPage = () => {
  const [startingYear, setStartingYear] = useState(null);
  const [graduationYear, setGraduationYear] = useState(null);
  const [school, setSchool] = useState([]);
  const [major, setMajor] = useState([]);
  const [minor, setMinor] = useState([]);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    setComplete(
      startingYear !== null &&
        graduationYear !== null &&
        school.length > 0 &&
        major.length > 0
    );
    console.log(startingYear);
    console.log(graduationYear);
    console.log(school);
    console.log(major);
    console.log(
      startingYear !== null &&
        graduationYear !== null &&
        school.length > 0 &&
        major.length > 0
    );
  }, [startingYear, graduationYear, school, major]);

  const startingYearOptions = [
    { value: "2024", label: "2024" },
    { value: "2023", label: "2023" },
    { value: "2022", label: "2022" },
    { value: "2021", label: "2021" },
  ];

  const endingYearOptions = [
    { value: "2027", label: "2027" },
    { value: "2026", label: "2026" },
    { value: "2025", label: "2025" },
    { value: "2024", label: "2024" },
  ];

  // const add_degree = (degreeplanId, degreeId) => {
  //   const updated = postFetcher(
  //     `/api/degree/degreeplans/${degreeplanId}/degrees`,
  //     { degree_ids: [degreeId] }
  //   ); // add degree
  //   mutate(`api/degree/degreeplans/${degreeplanId}`, updated, {
  //     populateCache: true,
  //     revalidate: false,
  //   }); // use updated degree plan returned
  //   mutate(
  //     (key) =>
  //       key &&
  //       key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`)
  //   ); // refetch the fulfillments
  // };

  // const { data: degreeplans, isLoading: isLoadingDegreeplans } = useSWR<
  //   DegreePlan[]
  // >("/api/degree/degreeplans");

  return (
    <Theme>
      <CenteredFlexContainer>
        <PanelContainer $maxWidth="1400px" $minWidth="1400px">
          <h1 style={{ paddingLeft: "100px", paddingTop: "50px" }}>
            Degree Information
          </h1>
          <ColumnsContainer>
            <Column>
              <Label required>Starting Year</Label>
              <Select
                options={yearOptions}
                value={startingYear}
                onChange={(selectedOption) => setStartingYear(selectedOption)}
                isClearable
                placeholder="Select Year Started"
                styles={customSelectStylesLeft}
              />

              <Label required>Graduation Year</Label>
              <Select
                options={yearOptions}
                value={graduationYear}
                onChange={(selectedOption) => setGraduationYear(selectedOption)}
                isClearable
                placeholder="Select Year of Graduation"
                styles={customSelectStylesLeft}
              />
            </Column>

            <Column>
              <Label required>School(s) or Program(s)</Label>
              <Select
                options={yearOptions}
                value={school}
                onChange={(selectedOption) => setSchool(selectedOption)}
                isClearable
                isMulti
                placeholder="Select School or Program"
                styles={customSelectStylesRight}
              />

              <Label required>Major(s)</Label>
              <Select
                options={yearOptions}
                value={major}
                onChange={(selectedOption) => setMajor(selectedOption)}
                isClearable
                isMulti
                placeholder="Major Name, Degree"
                styles={customSelectStylesRight}
              />

              <h5>Minor(s)</h5>
              <Select
                options={yearOptions}
                value={minor}
                onChange={(selectedOption) => setMinor(selectedOption)}
                isClearable
                isMulti
                placeholder="Minor Name"
                styles={customSelectStylesRight}
              />
            </Column>
          </ColumnsContainer>
          <NextButton
            color="blue"
            disabled={!complete}
            style={{
              height: "35px",
              width: "80px",
            }}
          >
            Next
          </NextButton>
        </PanelContainer>
      </CenteredFlexContainer>
    </Theme>
  );
};

export default OnboardingPage;
