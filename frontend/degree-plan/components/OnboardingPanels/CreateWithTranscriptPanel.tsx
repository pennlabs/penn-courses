import { ArrowLeftIcon } from "@radix-ui/react-icons";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
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
  schoolOptions,
  TextButton,
  TextInput,
} from "./SharedComponents";
import Select from "react-select";
import { PulseLoader } from "react-spinners";
import {
  DegreeListing,
  DegreePlan,
  MajorOption,
  Options,
  SchoolOption,
} from "@/types";
import useSWR from "swr";
import {
  getLocalSemestersKey,
  interpolateSemesters,
} from "@/components/FourYearPlan/Semesters";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { postFetcher, getCsrf } from "@/hooks/swrcrud";
import { getMajorOptions } from "@/utils/parseUtils";

type WelcomeLayoutProps = {
  inputtedStartingYear: { value: number; label: number } | null;
  inputtedGraduationYear: { value: number; label: number } | null;
  scrapedCourses: any;
  setCurrentPage: Dispatch<SetStateAction<number>>;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
  inputtedSchools: SchoolOption[];
  inputtedMajors: MajorOption[];
  setShowOnboardingModal: (arg0: boolean) => void;
};

export default function CreateWithTranscriptPanel({
  inputtedStartingYear,
  inputtedGraduationYear,
  scrapedCourses,
  setCurrentPage,
  setActiveDegreeplan,
  inputtedSchools,
  inputtedMajors,
  setShowOnboardingModal,
}: WelcomeLayoutProps) {
  const [startingYear, setStartingYear] = useState<{
    label: any;
    value: number;
  } | null>(inputtedStartingYear);
  const [graduationYear, setGraduationYear] = useState<{
    label: any;
    value: number;
  } | null>(inputtedGraduationYear);

  const [schools, setSchools] = useState<SchoolOption[]>(inputtedSchools);
  const [majors, setMajors] = useState<MajorOption[]>(inputtedMajors);
  const [degreeID, setDegreeID] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");

  const [nameAlreadyExists, setNameAlreadyExists] = useState(false);

  const { data: options } = useSWR<Options>("/api/options");
  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);

  // Workaround solution to only input courses once degree has been created and degreeID exists.
  // Will likely change in the future!
  useEffect(() => {
    if (degreeID) {
      const courses = [];
      for (let semester of scrapedCourses) {
        const formattedSemester: { sem: String; courses: String[] } = {
          sem: "",
          courses: [],
        };
        let rawSem = semester.sem;
        if (rawSem === "_TRAN") {
          formattedSemester.sem = "_TRAN";
        } else {
          let formattedSem = rawSem.match(/(\d+)/)[0];

          if (rawSem.includes("spring")) formattedSem += "A";
          else if (rawSem.includes("summer")) formattedSem += "B";
          else formattedSem += "C";
          formattedSemester.sem = formattedSem;
        }
        formattedSemester.courses = semester.courses.map((course: String) =>
          course.replace(" ", "-").toUpperCase()
        );
        courses.push(formattedSemester);
      }

      if (courses.length == 0) {
        setShowOnboardingModal(false);
      } else {
        postFetcher(`/api/degree/onboard-from-transcript/${degreeID}`, {
          courses: courses,
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
        postFetcher(`/api/degree/degreeplans/${_new.id}/degrees`, {
          degree_ids: majors.map((m) => m.value.id),
        }); // add degree
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
    schools.length > 0 &&
    majors.length > 0 &&
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

  const startingYearOptions = getYearOptions()?.startYears;
  const graduationYearOptions = getYearOptions()?.gradYears;

  const majorOptionsCallback = useCallback(() => {
    const majorOptions = getMajorOptions(degrees, schools, startingYear?.value ?? null);
    return majorOptions;
  }, [schools, startingYear]);

  return (
    <CenteredFlexContainer>
      <PanelContainer $maxWidth="90%" $minWidth="90%">
        <TextButton
          onClick={() => {
            setCurrentPage(0);
          }}
          style={{ marginLeft: "5%", marginTop: "3%" }}
        >
          <ArrowLeftIcon />
          <p>Back</p>
        </TextButton>
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
                options={majorOptionsCallback()}
                value={majors}
                onChange={(selectedOptions) => setMajors([...selectedOptions])}
                isClearable
                isMulti
                isDisabled={schools.length === 0}
                placeholder={"Major - Concentration"}
                styles={customSelectStylesRight}
                isLoading={isLoadingDegrees}
              />
            </FieldWrapper>

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
