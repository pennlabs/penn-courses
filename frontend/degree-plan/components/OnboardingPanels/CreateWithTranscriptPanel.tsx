import { ArrowLeftIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
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
import Select from "react-select";
import { PulseLoader } from "react-spinners";
import {
  DegreeListing,
  DegreePlan,
  Major,
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
import {
  CourseLevel,
  getMajorOptions,
  getSecondMajorOptions,
  MajorOptionItem,
} from "@/utils/parseUtils";

type ScrapedSemester = { sem: string; courses: string[] };

const RecordHeading = styled.h3`
  margin: 0.5rem 0 0;
  font-size: 1.1rem;
`;

const RecordNote = styled.p`
  margin: 0;
  font-size: 0.85rem;
  color: #666;
`;

const SHARED_COURSE_BACKGROUND = "#d6ebdf";

const courseChipStyles = {
  ...customSelectStylesCourses,
  multiValue: (provided: any, { data }: any) => ({
    ...customSelectStylesCourses.multiValue(provided),
    ...(data.shared ? { backgroundColor: SHARED_COURSE_BACKGROUND } : {}),
  }),
};

const semesterLabel = (sem: string) =>
  sem === "_TRAN" ? "Transfer Credit" : sem[0].toUpperCase() + sem.slice(1);

const RECORDS: { title: string; counts: (level?: CourseLevel) => boolean }[] = [
  { title: "Bachelors", counts: (level) => level !== "GRADUATE" },
  { title: "Masters", counts: (level) => level === "GRADUATE" || level === "SHARED" },
];

const SemesterRows = ({
  semesters,
  courseLevels,
  loading,
}: {
  semesters: ScrapedSemester[];
  courseLevels: { [course: string]: CourseLevel };
  loading: boolean;
}) => (
  <>
    {semesters.map((semester) => {
      const chips = semester.courses.map((course) => ({
        value: course.toUpperCase(),
        label: course.toUpperCase(),
        shared: courseLevels[course] === "SHARED",
      }));
      return (
        <FieldWrapper style={{ display: "flex" }} key={semester.sem}>
          <Label required={false}>{semesterLabel(semester.sem)}</Label>
          <Select
            components={{ MultiValueRemove: () => null }}
            options={chips}
            value={chips}
            isMulti
            placeholder="Courses"
            styles={courseChipStyles}
            isLoading={loading}
            isDisabled
          />
        </FieldWrapper>
      );
    })}
  </>
);

type WelcomeLayoutProps = {
  inputtedStartingYear: { value: number; label: number } | null;
  inputtedGraduationYear: { value: number; label: number } | null;
  scrapedCourses: any;
  // Which transcript record each scraped course is on; empty unless the transcript has a
  // masters record.
  courseLevels?: { [course: string]: CourseLevel };
  setCurrentPage: Dispatch<SetStateAction<number>>;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
  inputtedSchools: SchoolOption[];
  inputtedMajors: MajorOption[];
  setShowOnboardingModal: (arg0: boolean) => void;
  inputtedSecondMajors: MajorOptionItem[];
  canExit?: boolean;
  onExit?: () => void;
};

export default function CreateWithTranscriptPanel({
  inputtedStartingYear,
  inputtedGraduationYear,
  scrapedCourses,
  courseLevels = {},
  setCurrentPage,
  setActiveDegreeplan,
  inputtedSchools,
  inputtedMajors,
  inputtedSecondMajors,
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

  const [schools, setSchools] = useState<SchoolOption[]>(inputtedSchools);
  const [majors, setMajors] = useState<MajorOption[]>(inputtedMajors);
  const [secondMajors, setSecondMajors] =
    useState<MajorOptionItem[]>(inputtedSecondMajors);
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
      const toFullCode = (course: string) => course.replace(" ", "-").toUpperCase();
      const levels = Object.fromEntries(
        Object.entries(courseLevels).map(([course, level]) => [toFullCode(course), level])
      );
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
          courses: semester.courses.map(toFullCode),
        };
      });

      if (courses.length === 0) {
        setShowOnboardingModal(false);
      } else {
        postFetcher(`/api/degree/onboard-from-transcript/${degreeID}`, {
          courses,
          levels,
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
          degree_ids: majors.map((m) => m.value.id),
        });
        if (secondMajors.length) {
          await postFetcher(`/api/degree/degreeplans/${_new.id}/majors`, {
            major_ids: secondMajors.map((m) => m.value.id),
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

  const { startYears: startingYearOptions, gradYears: graduationYearOptions } = getYearOptions();

  const majorOptions = useMemo(
    () => getMajorOptions(degrees, schools, startingYear?.value ?? null),
    [degrees, schools, startingYear]
  );

  const secondMajorOptions = useMemo(
    () => getSecondMajorOptions(standaloneMajors, startingYear?.value ?? null),
    [standaloneMajors, startingYear]
  );

  const levels = Object.values(courseLevels);
  const hasMastersRecord = levels.some((level) => level !== "UNDERGRADUATE");
  const hasSharedCourses = levels.some((level) => level === "SHARED");
  const records: { title: string | null; semesters: ScrapedSemester[] }[] = hasMastersRecord
    ? RECORDS.map(({ title, counts }) => ({
        title,
        semesters: scrapedCourses
          .map((semester: ScrapedSemester) => ({
            ...semester,
            courses: semester.courses.filter((course) => counts(courseLevels[course])),
          }))
          .filter((semester: ScrapedSemester) => semester.courses.length > 0),
      }))
    : [{ title: null, semesters: scrapedCourses }];


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
                options={majorOptions}
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

            <FieldWrapper>
              <Label required={false}>Additional Major(s)</Label>
              <Select
                options={secondMajorOptions}
                value={secondMajors}
                onChange={(selectedOptions) =>
                  setSecondMajors([...selectedOptions])
                }
                isClearable
                isMulti
                placeholder="Major pursued alongside your degree"
                styles={customSelectStylesRight}
                isLoading={isLoadingMajors}
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
                {records.map(({ title, semesters }) => (
                  <section key={title ?? "courses"} aria-label={title ?? "Your courses"}>
                    {title && <RecordHeading>{title}</RecordHeading>}
                    {title === "Masters" && hasSharedCourses && (
                      <RecordNote>
                        Highlighted courses are on both records and count toward both degrees.
                      </RecordNote>
                    )}
                    <SemesterRows
                      semesters={semesters}
                      courseLevels={courseLevels}
                      loading={isLoadingDegrees}
                    />
                  </section>
                ))}
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
