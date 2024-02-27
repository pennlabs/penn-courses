import React, { useState, useEffect } from "react";
import { Button } from "@radix-ui/themes";
import { PlusIcon } from "@radix-ui/react-icons";
import { Theme } from "@radix-ui/themes";
import styled from "@emotion/styled";
import useSWR, { mutate } from "swr";
import Select from "react-select";
import { DegreeListing, DegreePlan, MajorOption, SchoolOption } from "@/types";
import { postFetcher, useSWRCrud } from "@/hooks/swrcrud";

const PanelContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
  border-radius: 10px;
  box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
  background-color: #ffffff;
  margin: 1rem;
  height: 85%;
  overflow: hidden; /* Hide scrollbars */
  width: ${(props) => (props.$maxWidth || props.$maxWidth ? "auto" : "100%")};
  max-width: ${(props) => (props.$maxWidth ? props.$maxWidth : "auto")};
  min-width: ${(props) => (props.$minWidth ? props.$minWidth : "auto")};
  position: relative;
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
  padding-top: 1.6rem;
  padding-left: 100px;
  gap: 20px;
  height: 100%;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

export const Column = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 2rem;
  padding-right: 3rem;
  
`;

const NextButtonContainer = styled.div`
  padding-top: 3rem;
  padding-right: 6rem;
  display: flex;
  flex-direction: row;
  justify-content: end;
`

const NextButton = styled(Button)`
  
  background-color: var(--primary-color-dark);
`;

export const Label = styled.h5`
  padding-top: 25px;
  &:after {
    content: "*";
    color: red;
    display: ${({ required }) => (required ? "inline" : "none")};
  }
`;

const TextInput = styled.input`
  padding: 2px 6px;
  width: 60%;
  height: 40%;
  border-radius: 3px;
  border-style: solid;
`

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
    width: 500,
    minHeight: "35px",
    height: "35px",
  }),
  menu: (provided) => ({
    ...provided,
    width: 500,
    maxHeight: '85rem',
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

const OnboardingPage = ({setShowOnboardingModal, setActiveDegreeplanId} : {setShowOnboardingModal: (arg0: boolean) => void, setActiveDegreeplanId: (arg0: number) => void }) => {
  const [startingYear, setStartingYear] = useState(null);
  const [graduationYear, setGraduationYear] = useState(null);
  const [schools, setSchools] = useState<SchoolOption[]>([]);
  const [majors, setMajors] = useState<MajorOption[]>([]);
  const [concentrations, setConcentrations] = useState([]);
  const [minor, setMinor] = useState([]);
  const [complete, setComplete] = useState(false);
  const [name, setName] = useState("");

  const { create: createDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
  
  useEffect(() => {
    setComplete(
      startingYear !== null &&
        graduationYear !== null &&
        schools.length > 0 &&
        majors.length > 0 &&
        name !== ""
    );
  }, [startingYear, graduationYear, schools, majors, name]);

  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);

  const startingYearOptions = [
    { value: "2024", label: "2024" },
    { value: "2023", label: "2023" },
    { value: "2022", label: "2022" },
    { value: "2021", label: "2021" },
  ];

  const graduationYearOptions = [
    { value: "2027", label: "2027" },
    { value: "2026", label: "2026" },
    { value: "2025", label: "2025" },
    { value: "2024", label: "2024" },
  ];

  const defaultSchools = ['BSE', 'BA', 'BAS', 'BS'];

  const schoolOptions =
    defaultSchools.map((d) => ({
      value: d,
      label: d
    }))
  // console.log('schooOptions', schoolOptions);

  /** Create label for major listings */
  const createMajorLabel = (degree: DegreeListing) => {
    const concentration = 
      degree.concentration && degree.concentration !== 'NONE' 
        ? ` - ${degree.concentration}`
        : '';
    return `${degree.major}${concentration}`;
  }

  const getMajorOptions = React.useCallback(() => {
    /** Filter major options based on selected schools/degrees */
    const majorOptions = degrees
      ?.filter(d => schools.map(s => s.value).includes(d.degree))
      .map((degree) => ({ value: degree, label: createMajorLabel(degree)})) 
      || [];
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
    .catch(e => alert('Trouble adding degrees: ' + e))
    .then((res) => {
      if (res) {
        setActiveDegreeplanId(res.id)
        console.log('arguments to the route', [majors.map(m => m.value.id)]);
        console.log('post new degrees for degree plan with id ', res.id);
        const updated = postFetcher(`/api/degree/degreeplans/${res.id}/degrees`, { degree_ids: majors.map(m => m.value.id) }) // add degree
        // mutate(`api/degree/degreeplans/${res.id}`, updated, { populateCache: true, revalidate: false }) // use updated degree plan returned
        // mutate(key => key && key.startsWith(`/api/degree/degreeplans/${res.id}/fulfillments`)) // refetch the fulfillments  
        setShowOnboardingModal(false);
      }
    })
}

  return (
      <CenteredFlexContainer>
        <PanelContainer $maxWidth="1400px" $minWidth="1400px">
          <h1 style={{ paddingLeft: "100px", paddingTop: "50px" }}>
            Degree Information
          </h1>
          <ColumnsContainer>
            <Column>
              <div>
                <Label required>Starting Year</Label>
                <Select
                  options={startingYearOptions}
                  value={startingYear}
                  onChange={(selectedOption) => setStartingYear(selectedOption)}
                  isClearable
                  placeholder="Select Year Started"
                  styles={customSelectStylesLeft}
                />
              </div>

              <div>
                <Label required>Graduation Year</Label>
                <Select
                  options={graduationYearOptions}
                  value={graduationYear}
                  onChange={(selectedOption) => setGraduationYear(selectedOption)}
                  isClearable
                  placeholder="Select Year of Graduation"
                  styles={customSelectStylesLeft}
                />
              </div>

              <div>
                <Label required>Default Plan Name</Label>
                <TextInput value={name} onChange={(e) => setName(e.target.value)} placeholder=""/>
              </div>
            </Column>

            <Column>
              <div>
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
              </div>

              <div>
                <Label required>Major(s)</Label>
                <Select
                  options={getMajorOptions()}
                  value={majors}
                  onChange={(selectedOption) => setMajors(selectedOption)}
                  isClearable
                  isMulti
                  placeholder={schools.length > 0 ? "Major - Concentration" : "Please Select Program First"}
                  styles={customSelectStylesRight}
                  isLoading={isLoadingDegrees}
                />
              </div>

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
