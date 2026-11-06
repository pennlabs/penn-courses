import { ArrowLeftIcon } from "@radix-ui/react-icons";
import { Dispatch, SetStateAction, useCallback, useEffect, useState } from "react";
import { BackButton, NextButton } from "./SharedComponents";
import Select from "react-select";
import { PulseLoader } from "react-spinners";
import { DegreeListing, DegreePlan, Major, Minor, Options } from "@/types";
import useSWR from "swr";
import {
  getLocalSemestersKey,
  interpolateSemesters,
} from "@/components/FourYearPlan/Semesters";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { postFetcher, getCsrf } from "@/hooks/swrcrud";
import { CourseLevel, SchoolSelection } from "@/utils/parseUtils";
import { Field, FieldGrid, FieldLabel, Required, selectStyles } from "./onboardingStyles";
import {
  Body,
  Card,
  FieldError,
  Footer,
  Header,
  Page,
  ScrollArea,
  ScrollContent,
  Section,
  TextInput,
  Title,
} from "./formLayout";
import SchoolsField from "./SchoolsField";
import ImportedCourses from "./ImportedCourses";

type WelcomeLayoutProps = {
  inputtedStartingYear: { value: number; label: number } | null;
  inputtedGraduationYear: { value: number; label: number } | null;
  scrapedCourses: any;
  // Which transcript record each scraped course is on; empty unless the transcript has a
  // masters record.
  courseLevels?: { [course: string]: CourseLevel };
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
  courseLevels = {},
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
  const { data: minors, isLoading: isLoadingMinors } = useSWR<Minor[]>(`/api/degree/minors`);

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
          degree_ids: selections.flatMap((s) => (s.primary ? [s.primary.value.id] : [])),
        });
        for (const selection of selections.filter((s) => s.additional.length)) {
          // Each post reallocates the whole plan, so they must not overlap.
          // eslint-disable-next-line no-await-in-loop
          await postFetcher(`/api/degree/degreeplans/${_new.id}/majors`, {
            major_ids: selection.additional.map((m) => m.value.id),
            degree_id: selection.primary?.value.id,
          });
        }
        for (const selection of selections.filter((s) => s.minors?.length)) {
          // eslint-disable-next-line no-await-in-loop
          await postFetcher(`/api/degree/degreeplans/${_new.id}/minors`, {
            minor_ids: selection.minors!.map((m) => m.value.id),
            degree_id: selection.primary?.value.id,
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

  return (
    <Page>
      <Card>
        <ScrollArea>
          <ScrollContent>
            <Header>
              <BackButton type="button" onClick={() => setCurrentPage(0)}>
                <ArrowLeftIcon width={16} height={16} />
                Back
              </BackButton>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <Title>Set up your degree plan</Title>
                <ImportedCourses scrapedCourses={scrapedCourses} courseLevels={courseLevels} />
              </div>
            </Header>

            <Body>
              <Section>
                <Field>
                  <FieldLabel htmlFor="plan-name">
                    Plan name
                    <Required />
                  </FieldLabel>
                  <TextInput
                    id="plan-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. My Degree Plan"
                    aria-invalid={nameAlreadyExists}
                    aria-describedby={nameAlreadyExists ? "plan-name-error" : undefined}
                  />
                  {nameAlreadyExists && (
                    <FieldError id="plan-name-error" role="alert">
                      A degree plan with this name already exists. Please choose a different name.
                    </FieldError>
                  )}
                </Field>
                <FieldGrid $min={200}>
                  <Field>
                    <FieldLabel htmlFor="start-year">
                      Starting year
                      <Required />
                    </FieldLabel>
                    <Select
                      inputId="start-year"
                      options={startingYearOptions}
                      value={startingYear}
                      onChange={(selectedOption) => setStartingYear(selectedOption)}
                      formatOptionLabel={(o) => `Fall ${o.value}`}
                      isClearable
                      placeholder="Select a year"
                      styles={selectStyles}
                      menuPortalTarget={typeof document !== "undefined" ? document.body : null}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="grad-year">
                      Graduation year
                      <Required />
                    </FieldLabel>
                    <Select
                      inputId="grad-year"
                      options={graduationYearOptions}
                      value={graduationYear}
                      onChange={(selectedOption) => setGraduationYear(selectedOption)}
                      formatOptionLabel={(o) => `Spring ${o.value}`}
                      isClearable
                      placeholder="Select a year"
                      styles={selectStyles}
                      menuPortalTarget={typeof document !== "undefined" ? document.body : null}
                    />
                  </Field>
                </FieldGrid>
              </Section>

              <Section>
                <div>
                  <FieldLabel>
                    Schools &amp; majors
                    <Required />
                  </FieldLabel>
                </div>

                <SchoolsField
                  selections={selections}
                  setSelections={setSelections}
                  degrees={degrees}
                  standaloneMajors={standaloneMajors}
                  minors={minors}
                  isLoadingDegrees={isLoadingDegrees}
                  isLoadingMajors={isLoadingMajors}
                  isLoadingMinors={isLoadingMinors}
                />
              </Section>
            </Body>
          </ScrollContent>
        </ScrollArea>

        <Footer>
          <NextButton onClick={handleAddDegrees} disabled={!complete || loading}>
            {loading ? <PulseLoader size={8} color="white" /> : "Next"}
          </NextButton>
        </Footer>
      </Card>
    </Page>
  );
}
