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
import Select from "react-select";
import { PulseLoader } from "react-spinners";
import {
  DegreeListing,
  DegreePlan,
  DualProgram,
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
  getMajorOptions,
  getSecondMajorOptions,
  MajorOptionItem,
} from "@/utils/parseUtils";

type WelcomeLayoutProps = {
  inputtedStartingYear: { value: number; label: number } | null;
  inputtedGraduationYear: { value: number; label: number } | null;
  scrapedCourses: any;
  setCurrentPage: Dispatch<SetStateAction<number>>;
  setActiveDegreeplan: (arg0: DegreePlan) => void;
  inputtedSchools: SchoolOption[];
  inputtedMajors: MajorOption[];
  setShowOnboardingModal: (arg0: boolean) => void;
  inputtedSecondMajors: MajorOptionItem[];
  detectedDualProgram?: string | null;
  canExit?: boolean;
  onExit?: () => void;
};

export default function CreateWithTranscriptPanel({
  inputtedStartingYear,
  inputtedGraduationYear,
  scrapedCourses,
  setCurrentPage,
  setActiveDegreeplan,
  inputtedSchools,
  inputtedMajors,
  inputtedSecondMajors,
  detectedDualProgram = null,
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
  const [dualProgram, setDualProgram] = useState<DualProgram | null>(null);
  const [leftDegree, setLeftDegree] = useState<DegreeListing | null>(null);
  const [rightDegree, setRightDegree] = useState<DegreeListing | null>(null);
  const [languageRequired, setLanguageRequired] = useState(false);
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
  const { data: dualPrograms } = useSWR<DualProgram[]>(`/api/degree/dual-programs`);

  useEffect(() => {
    if (!detectedDualProgram || !dualPrograms || dualProgram) return;
    const match = dualPrograms.find((program) => program.code === detectedDualProgram);
    if (match) setDualProgram(match);
  }, [detectedDualProgram, dualPrograms, dualProgram]);

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
        if (dualProgram && leftDegree && rightDegree) {
          await postFetcher(`/api/degree/degreeplans/${_new.id}/dual-program`, {
            code: dualProgram.code,
            left_id: leftDegree.id,
            right_id: rightDegree.id,
            ...(dualProgram.code === "MT" && languageRequired
              ? { right_variant: "WH_FL_MT" }
              : {}),
          });
        } else {
          await postFetcher(`/api/degree/degreeplans/${_new.id}/degrees`, {
            degree_ids: majors.map((m) => m.value.id),
          });
          if (secondMajors.length) {
            await postFetcher(`/api/degree/degreeplans/${_new.id}/majors`, {
              major_ids: secondMajors.map((m) => m.value.id),
            });
          }
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

  const degreesChosen = dualProgram
    ? leftDegree !== null && rightDegree !== null
    : schools.length > 0 && majors.length > 0;
  const complete =
    startingYear !== null &&
    graduationYear !== null &&
    degreesChosen &&
    name !== "";

  const sideOptions = (programs: string[], allowedMajors: string[]) =>
    (degrees ?? [])
      .filter(
        (degree) =>
          programs.includes(degree.program) &&
          (allowedMajors.length === 0 || allowedMajors.includes(degree.major))
      )
      .map((degree) => ({
        value: degree,
        label: `${degree.major_name || degree.major}${
          degree.concentration_name ? ` - ${degree.concentration_name}` : ""
        } (${degree.year})`,
      }))
      .sort((a, b) => a.label.localeCompare(b.label));

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

              <Label required={false}>Dual-degree program</Label>
              <Select
                options={[
                  { value: null, label: "None" },
                  ...(dualPrograms ?? []).map((program) => ({
                    value: program,
                    label: program.name,
                  })),
                ]}
                value={
                  dualProgram
                    ? { value: dualProgram, label: dualProgram.name }
                    : { value: null, label: "None" }
                }
                onChange={(selected) => {
                  setDualProgram(selected?.value ?? null);
                  setLeftDegree(null);
                  setRightDegree(null);
                }}
                placeholder="None"
                styles={customSelectStylesRight}
              />
            </FieldWrapper>

            {dualProgram && (
              <>
                <FieldWrapper>
                  <Label required>{dualProgram.name.split(" ")[0]} — first degree</Label>
                  <Select
                    options={sideOptions(dualProgram.left_programs, dualProgram.left_allowed_majors)}
                    value={
                      leftDegree
                        ? {
                            value: leftDegree,
                            label: leftDegree.major_name || leftDegree.major,
                          }
                        : null
                    }
                    onChange={(selected) => setLeftDegree(selected?.value ?? null)}
                    placeholder="Select the first degree"
                    styles={customSelectStylesRight}
                  />
                </FieldWrapper>
                <FieldWrapper>
                  <Label required>Second degree</Label>
                  <Select
                    options={sideOptions(
                      dualProgram.right_programs,
                      dualProgram.right_allowed_majors
                    )}
                    value={
                      rightDegree
                        ? {
                            value: rightDegree,
                            label: rightDegree.major_name || rightDegree.major,
                          }
                        : null
                    }
                    onChange={(selected) => setRightDegree(selected?.value ?? null)}
                    placeholder="Select the second degree"
                    styles={customSelectStylesRight}
                  />
                </FieldWrapper>
                {dualProgram.code === "MT" && (
                  <FieldWrapper>
                    <label>
                      <input
                        type="checkbox"
                        checked={languageRequired}
                        onChange={(event) => setLanguageRequired(event.target.checked)}
                      />{" "}
                      Foreign language required
                    </label>
                  </FieldWrapper>
                )}
              </>
            )}

            {!dualProgram && (
            <>
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
            </>
            )}

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
