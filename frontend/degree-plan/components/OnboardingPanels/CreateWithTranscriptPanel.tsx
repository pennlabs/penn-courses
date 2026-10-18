import { ArrowLeftIcon, PlusIcon } from "@radix-ui/react-icons";
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
  NextButton,
  panelCard,
  schoolOptions,
} from "./SharedComponents";
import styled from "@emotion/styled";
import Select, { StylesConfig } from "react-select";
import { PulseLoader } from "react-spinners";
import { DegreeListing, DegreePlan, Major, Options } from "@/types";
import useSWR from "swr";
import {
  getLocalSemestersKey,
  interpolateSemesters,
} from "@/components/FourYearPlan/Semesters";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { postFetcher, getCsrf } from "@/hooks/swrcrud";
import { SchoolSelection } from "@/utils/parseUtils";
import {
  color,
  Field,
  FieldGrid,
  FieldLabel,
  Required,
  selectStyles,
} from "./onboardingStyles";
import SchoolCard from "./SchoolCard";
import ImportedCourses from "./ImportedCourses";

const Page = styled(CenteredFlexContainer)`
  overflow: hidden;
  color: ${color.text};
`;

const contentMaxWidth = 1200;
const contentWidth = `
  width: 100%;
  max-width: ${contentMaxWidth}px;
  margin: 0 auto;
  box-sizing: border-box;
`;

const Card = styled.div`
  ${panelCard}
  width: 90%;
  height: 85%;
  overflow: hidden;
  box-sizing: border-box;
  border: 1px solid ${color.border};
  display: flex;
  flex-direction: column;
`;

const ScrollArea = styled.div`
  flex: 1;
  position: relative;
`;

const ScrollContent = styled.div`
  position: absolute;
  inset: 0;
  overflow-y: auto;
`;

const Header = styled.div`
  ${contentWidth}
  padding: 32px 40px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;

  @media (max-width: 600px) {
    padding: 24px 16px 0;
  }
`;

const BackButton = styled.button`
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  color: ${color.muted};
  cursor: pointer;

  &:hover {
    color: ${color.text};
  }
`;

const Title = styled.h1`
  margin: 0;
  font-size: 32px;
  line-height: 1.15;
  font-weight: 700;
`;

const Body = styled.div`
  ${contentWidth}
  display: flex;
  flex-direction: column;
  gap: 36px;
  padding: 32px 40px 40px;

  @media (max-width: 600px) {
    padding: 24px 16px 32px;
  }
`;

const FormColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 36px;
`;

const Section = styled.section`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const TextInput = styled.input`
  height: 44px;
  padding: 0 14px;
  border: 1px solid ${color.inputBorder};
  border-radius: 8px;
  font: inherit;
  font-size: 15px;
  color: ${color.text};
  background: #ffffff;
  box-sizing: border-box;
  width: 100%;

  &::placeholder {
    color: ${color.subtle};
  }

  &:focus {
    outline: none;
    border-color: ${color.accent};
    box-shadow: 0 0 0 3px rgba(47, 79, 216, 0.15);
  }
`;

const ErrorText = styled.p`
  margin: 0;
  font-size: 13px;
  color: ${color.required};
`;

const SchoolList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

// Groups the add button and the school cards; matches the imported-courses box.
const SchoolsBox = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #f8f9fb;
  border: 1px solid ${color.border};
  border-radius: 12px;
`;

const AddSchoolButton = styled.button`
  min-height: 52px;
  border: 1.5px dashed #c4c9d2;
  border-radius: 12px;
  background: #ffffff;
  font: inherit;
  font-size: 15px;
  font-weight: 500;
  color: ${color.accent};
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;

  &:hover {
    border-color: ${color.accent};
    background: #f5f7ff;
  }
`;

const Footer = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  // Divider spans the card; the button lines up with the capped content above.
  padding: 20px max(40px, calc((100% - ${contentMaxWidth}px) / 2 + 40px));
  border-top: 1px solid ${color.border};
  background: #fcfcfd;
  border-radius: 0 0 10px 10px;

  @media (max-width: 600px) {
    padding: 16px;
  }
`;

// The school picker replaces AddSchoolButton in place, so it takes the button's size and corners.
const addSchoolSelectStyles: StylesConfig<any, boolean> = {
  ...selectStyles,
  control: (provided, state) => ({
    ...selectStyles.control!(provided, state),
    minHeight: 52,
    borderRadius: 12,
  }),
};

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
  const [addingSchool, setAddingSchool] = useState(false);
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
  // a different year. A school with its own start year (a submatriculant's masters) keeps its
  // majors, since they don't follow the plan's.
  useEffect(() => {
    const year = startingYear?.value;
    setSelections((current) =>
      current.map((s) =>
        s.startYear
          ? s
          : {
              ...s,
              primary: s.primary?.value.year === year ? s.primary : null,
              additional: s.additional.filter((m) => m.value.year === year),
            }
      )
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
                <ImportedCourses scrapedCourses={scrapedCourses} />
              </div>
            </Header>

            <Body>
              <FormColumn>
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
                      <ErrorText id="plan-name-error" role="alert">
                        A degree plan with this name already exists. Please choose a different name.
                      </ErrorText>
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

                  <SchoolsBox>
                    {addableSchools.length > 0 &&
                      (addingSchool ? (
                        <Select
                          aria-label="Add a school or program"
                          options={addableSchools}
                          value={null}
                          onChange={(selected) => {
                            if (selected)
                              setSelections((current) => [
                                { school: selected, primary: null, additional: [] },
                                ...current,
                              ]);
                            setAddingSchool(false);
                          }}
                          onMenuClose={() => setAddingSchool(false)}
                          autoFocus
                          defaultMenuIsOpen
                          placeholder="Choose a school or program"
                          styles={addSchoolSelectStyles}
                          menuPortalTarget={typeof document !== "undefined" ? document.body : null}
                          isLoading={isLoadingDegrees}
                        />
                      ) : (
                        <AddSchoolButton type="button" onClick={() => setAddingSchool(true)}>
                          <PlusIcon width={16} height={16} />
                          Add a school or program
                        </AddSchoolButton>
                      ))}

                    {selections.length > 0 && (
                      <SchoolList role="region" aria-label="Your schools">
                        {selections.map((selection) => (
                          <SchoolCard
                            key={selection.school.value}
                            selection={selection}
                            startingYear={selection.startYear ?? startingYear?.value ?? null}
                            degrees={degrees}
                            standaloneMajors={standaloneMajors}
                            isLoadingDegrees={isLoadingDegrees}
                            isLoadingMajors={isLoadingMajors}
                            onChange={(changes) => updateSelection(selection.school, changes)}
                            onRemove={() =>
                              setSelections((current) =>
                                current.filter((s) => s.school.value !== selection.school.value)
                              )
                            }
                          />
                        ))}
                      </SchoolList>
                    )}
                  </SchoolsBox>
                </Section>
              </FormColumn>
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
