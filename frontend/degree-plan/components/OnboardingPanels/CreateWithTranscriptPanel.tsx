import { ArrowLeftIcon } from "@radix-ui/react-icons";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  CenteredFlexContainer,
  Column,
  ColumnsContainer,
  CourseContainer,
  ErrorText,
  customSelectStylesCourses,
  customSelectStylesLeft,
  customSelectStylesRight,
  FieldWrapper,
  Label,
  NextButton,
  NextButtonContainer,
  PanelContainer,
  TextButton,
  TextInput,
  schoolOptions,
} from "./SharedComponents";
import styled from "@emotion/styled";
import Select from "react-select";
import { PulseLoader } from "react-spinners";
import { DegreeListing, DegreePlan, Major, Options } from "@/types";
import useSWR from "swr";
import {
  getLocalSemestersKey,
  interpolateSemesters,
} from "@/components/FourYearPlan/Semesters";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { postFetcher, getCsrf } from "@/hooks/swrcrud";
import {
  getAdditionalMajorOptions,
  getMajorOptions,
  SchoolSelection,
} from "@/utils/parseUtils";

const SchoolCard = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.75rem 1rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
`;

const SchoolCardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

type WelcomeLayoutProps = {
  inputtedStartingYear: { value: number; label: number } | null;
  inputtedGraduationYear: { value: number; label: number } | null;
  scrapedCourses: any;
  setCurrentPage: Dispatch<SetStateAction<number>>;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
  inputtedSelections: SchoolSelection[];
  setShowOnboardingModal: (arg0: boolean) => void;
  canExit?: boolean;
  onExit?: () => void;
};

export default function CreateWithTranscriptPanel({
  inputtedStartingYear,
  inputtedGraduationYear,
  scrapedCourses,
  setCurrentPage,
  setActiveDegreeplan,
  inputtedSelections,
  setShowOnboardingModal,
  canExit = false,
  onExit,
}: WelcomeLayoutProps) {
  const [startingYear, setStartingYear] = useState<{
    label: any;
    value: number;
  } | null>(inputtedStartingYear);
  const [graduationYear, setGraduationYear] = useState<{
    label: any;
    value: number;
  } | null>(inputtedGraduationYear);

  const [selections, setSelections] =
    useState<SchoolSelection[]>(inputtedSelections);
  const [degreeID, setDegreeID] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");

  const [nameAlreadyExists, setNameAlreadyExists] = useState(false);

  const { data: options } = useSWR<Options>("/api/options");
  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);
  const { data: standaloneMajors, isLoading: isLoadingMajors } =
    useSWR<Major[]>(`/api/degree/majors`);

  // Workaround solution to only input courses once degree has been created and degreeID exists.
  // Will likely change in the future!
  useEffect(() => {
    if (degreeID) {
      const courses = scrapedCourses.map((semester: any) => {
        const rawSem = semester.sem;
        let sem: string;
        if (rawSem === "_TRAN") {
          sem = "_TRAN";
        } else {
          const year = rawSem.match(/(\d+)/)[0];
          const suffix = rawSem.includes("spring") ? "A" : rawSem.includes("summer") ? "B" : "C";
          sem = year + suffix;
        }
        return {
          sem,
          courses: semester.courses.map((course: string) =>
            course.replace(" ", "-").toUpperCase()
          ),
        };
      });

      if (courses.length === 0) {
        setShowOnboardingModal(false);
      } else {
        postFetcher(`/api/degree/onboard-from-transcript/${degreeID}`, {
          courses,
        }).then((r) => setShowOnboardingModal(false));
      }
    }
  }, [degreeID]);

  const handleAddDegrees = () => {
    setLoading(true);

    const createDegreeplan = async () => {
      // Need to handle the case where degree plan of same name already exists.
      const res = await fetch("/api/degree/degreeplans", {
        credentials: "include",
        mode: "same-origin",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrf(),
          "Accept": "application/json",
        } as HeadersInit,
        body: JSON.stringify({ name: name }),
      });

      if (res.ok) {
        const _new = await res.json();
        if (startingYear && graduationYear) {
          const semesters = interpolateSemesters(
            startingYear.value,
            graduationYear.value
          );
          semesters[TRANSFER_CREDIT_SEMESTER_KEY] = [];
          window.localStorage.setItem(
            getLocalSemestersKey(_new.id),
            JSON.stringify(semesters)
          );
        }
        await postFetcher(`/api/degree/degreeplans/${_new.id}/degrees`, {
          degree_ids: selections.flatMap((s) => (s.primary ? [s.primary.value.id] : [])),
        });
        const additionalMajors = selections.flatMap((s) => s.additional);
        if (additionalMajors.length) {
          await postFetcher(`/api/degree/degreeplans/${_new.id}/majors`, {
            major_ids: additionalMajors.map((m) => m.value.id),
          });
        }
        setActiveDegreeplan(_new);
        setDegreeID(_new.id);
      } else if (res.status === 409) {
        // Case where degree plan of same name already exists.
        setNameAlreadyExists(true);
        setLoading(false);

        setTimeout(() => {
          setNameAlreadyExists(false);
        }, 5000);
      } else {
        console.error(await res.text());
      }
    }

    createDegreeplan().then(() => {});
  };

  const complete =
    startingYear !== null &&
    graduationYear !== null &&
    selections.length > 0 &&
    selections.every((s) => s.primary) &&
    name !== "";

  const getYearOptions = useCallback(() => {
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

  const { startYears: startingYearOptions, gradYears: graduationYearOptions } = getYearOptions();

  // Majors are held to the year the student started, so changing it drops any that belong to
  // a different year.
  useEffect(() => {
    const year = startingYear?.value;
    setSelections((current) =>
      current.map((s) => ({
        ...s,
        primary: s.primary?.value.year === year ? s.primary : null,
        additional: s.additional.filter((m) => m.value.year === year),
      }))
    );
  }, [startingYear?.value]);

  const updateSelection = (
    school: SchoolSelection["school"],
    changes: Partial<SchoolSelection>
  ) =>
    setSelections((current) =>
      current.map((s) => (s.school.value === school.value ? { ...s, ...changes } : s))
    );

  const addableSchools = useMemo(
    () =>
      schoolOptions.filter((o) => !selections.some((s) => s.school.value === o.value)),
    [selections]
  );


  return (
    <CenteredFlexContainer>
      <PanelContainer $maxWidth="90%" $minWidth="90%">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginLeft: "5%",
            marginRight: "5%",
            marginTop: "3%",
          }}
        >
          <TextButton
            onClick={() => {
              setCurrentPage(0);
            }}
          >
            <ArrowLeftIcon />
            <p>Back</p>
          </TextButton>
        </div>
        <ColumnsContainer>
          <Column>
            <h1 style={{ paddingTop: "1.25%" }}>Enter your degree(s):</h1>
            <FieldWrapper>
              <Label required>Degree Plan Name</Label>
              <TextInput
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder=""
              />
              {nameAlreadyExists && (
                <ErrorText
                  style={{
                    color: "red",
                    visibility: nameAlreadyExists ? "visible" : "hidden",
                  }}
                  >
                    A degree plan with this name already exists. Please choose a different name.
                  </ErrorText>
              )}
            </FieldWrapper>

            <FieldWrapper>
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
                  onChange={(selectedOption) =>
                    setGraduationYear(selectedOption)
                  }
                  isClearable
                  placeholder="Select Year of Graduation"
                  styles={customSelectStylesLeft}
                />
              </FieldWrapper>

              <Label required>School(s) or Program(s)</Label>
              <Select
                options={addableSchools}
                value={null}
                onChange={(selected) =>
                  selected &&
                  setSelections((current) => [
                    ...current,
                    { school: selected, primary: null, additional: [] },
                  ])
                }
                placeholder="Add a school or program"
                styles={customSelectStylesRight}
                isLoading={isLoadingDegrees}
              />
            </FieldWrapper>

            {selections.map(({ school, primary, additional }) => (
              <SchoolCard key={school.value}>
                <SchoolCardHeader>
                  <h4>{school.label}</h4>
                  <TextButton
                    onClick={() =>
                      setSelections((current) =>
                        current.filter((s) => s.school.value !== school.value)
                      )
                    }
                  >
                    Remove
                  </TextButton>
                </SchoolCardHeader>

                <FieldWrapper>
                  <Label required>Primary Major</Label>
                  <Select
                    options={getMajorOptions(degrees, school, startingYear?.value ?? null)}
                    value={primary}
                    onChange={(selected) =>
                      updateSelection(school, { primary: selected })
                    }
                    isClearable
                    isDisabled={!startingYear}
                    placeholder={
                      startingYear ? "Major - Concentration" : "Select your starting year first"
                    }
                    styles={customSelectStylesRight}
                    isLoading={isLoadingDegrees}
                  />
                </FieldWrapper>

                <FieldWrapper>
                  <Label required={false}>Additional Major(s)</Label>
                  <Select
                    options={getAdditionalMajorOptions(
                      standaloneMajors,
                      school,
                      startingYear?.value ?? null
                    )}
                    value={additional}
                    onChange={(selected) =>
                      updateSelection(school, { additional: [...selected] })
                    }
                    isClearable
                    isMulti
                    isDisabled={!startingYear}
                    placeholder="Major pursued alongside your primary major"
                    styles={customSelectStylesRight}
                    isLoading={isLoadingMajors}
                  />
                </FieldWrapper>
              </SchoolCard>
            ))}

            {!scrapedCourses.length && (
              <NextButtonContainer>
                <NextButton
                  onClick={handleAddDegrees}
                  disabled={!complete}
                  style={{
                    height: "35px",
                    width: "90px",
                    borderRadius: "7px",
                    color: "white",
                    transition: "all 0.25s",
                  }}
                >
                  {!loading && <div>Next</div>}
                  <PulseLoader size={8} color={"white"} loading={loading} />
                </NextButton>
              </NextButtonContainer>
            )}
          </Column>

          {scrapedCourses.length > 0 && (
            <Column>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 5,
                  paddingTop: "1.25%",
                }}
              >
                <h2>Your Courses</h2>
                <p>You can make edits on the next page.</p>
              </div>

              <CourseContainer>
                {scrapedCourses.map((e: any, i: number) => {
                  const semCourses = e.courses.map(
                    (course: any, _: any) =>
                      [
                        {
                          value: course.toUpperCase(),
                          label: course.toUpperCase(),
                        },
                      ][0]
                  );
                  return (
                    <FieldWrapper style={{ display: "flex" }} key={i}>
                      {e.sem === "_TRAN" ? (
                        <Label required={false}>Transfer Credit</Label>
                      ) : (
                        <Label required={false}>
                          {e.sem[0].toUpperCase() + e.sem.slice(1)}
                        </Label>
                      )}
                      <Select
                        components={{ MultiValueRemove: () => null }}
                        options={semCourses}
                        value={semCourses}
                        isMulti
                        placeholder="Courses"
                        styles={customSelectStylesCourses}
                        isLoading={isLoadingDegrees}
                        isDisabled
                      />
                    </FieldWrapper>
                  );
                })}
              </CourseContainer>
              <NextButtonContainer>
                <NextButton
                  onClick={handleAddDegrees}
                  disabled={!complete}
                  style={{
                    height: "35px",
                    width: "90px",
                    borderRadius: "7px",
                    color: "white",
                    transition: "all 0.25s",
                  }}
                >
                  {!loading && <div>Next</div>}
                  <PulseLoader size={8} color={"white"} loading={loading} />
                </NextButton>
              </NextButtonContainer>
            </Column>
          )}
        </ColumnsContainer>
      </PanelContainer>
    </CenteredFlexContainer>
  );
}
