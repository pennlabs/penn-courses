import React, { useState, useEffect, useRef } from "react";
import { Button } from "@radix-ui/themes";
import styled from "@emotion/styled";
import useSWR, { mutate } from "swr";
import Select from "react-select";
import { Document, Page, DocumentProps } from "react-pdf";
import { pdfjs } from "react-pdf";
import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";
import {
  DegreeListing,
  DegreePlan,
  DockedCourse,
  Fulfillment,
  MajorOption,
  Options,
  SchoolOption,
} from "@/types";
import { postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import {
  getLocalSemestersKey,
  interpolateSemesters,
} from "@/components/FourYearPlan/Semesters";
import { maxWidth, TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { polyfillPromiseWithResolvers } from "./polyfilsResolver";

import "core-js/full/promise/with-resolvers.js";
import {
  UploadIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
} from "@radix-ui/react-icons";
polyfillPromiseWithResolvers();

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.mjs`;

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

const ChooseContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
  padding-top: 5%;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
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
  gap: 1rem;
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

const NextButton = styled(Button)<{ disabled: boolean }>`
  background-color: ${({ disabled }) =>
    disabled ? "var(--primary-color-dark)" : "#0000ff"};

  @media (max-width: 768px) {
    width: 80%;
    margin: 0 auto;
  }
`;

const Upload = styled.div`
  width: 350px;
  height: 100px;
  border: 1px dashed #808080;
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  transition: all 0.25s;
  &:hover {
    background-color: #f6f6f6;
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
  { value: "BSN", label: "Nursing" },
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

const TextButton = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
  width: fit-content;
  border-bottom: 1px solid #aaaaaa00;
  &:hover {
    // text-decoration: underline;
    border-bottom: 1px solid #aaa;
    cursor: pointer;
  }
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

const customSelectStylesCourses = {
  control: (provided: any) => ({
    ...provided,
    width: "80%",
    minHeight: "35px",
    // height: "65px",
  }),
  menu: (provided: any) => ({
    ...provided,
    width: 500,
    maxHeight: "85rem",
  }),
  valueContainer: (provided: any) => ({
    ...provided,
    // height: "55px",
    // padding: "0 6px",
  }),
  input: (provided: any) => ({
    ...provided,
    margin: "0px",
  }),
  indicatorsContainer: (provided: any) => ({
    ...provided,
    // height: "65px",
    display: "none",
  }),
  multiValue: (provided: any) => ({
    ...provided,
    borderRadius: "8px",
    maxWidth: "200px",
    paddingRight: 4,
    marginRight: 3,
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
  const [startingYear, setStartingYear] = useState<{
    label: any;
    value: number;
  } | null>(null);
  const [graduationYear, setGraduationYear] = useState<{
    label: any;
    value: number;
  } | null>(null);
  const [schools, setSchools] = useState<SchoolOption[]>([]);
  const [majors, setMajors] = useState<MajorOption[]>([]);
  const [minor, setMinor] = useState([]);
  const [name, setName] = useState("");

  const [PDF, setPDF] = useState<File | null>(null);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [scrapedCourses, setScrapedCourses] = useState<any>([]);
  const [scrapedTransfer, setScrapedTransfer] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(0);

  const { create: createDegreeplan } = useSWRCrud<DegreePlan>(
    "/api/degree/degreeplans"
  );

  const [degreeID, setDegreeID] = useState<number | null>(null);

  const { createOrUpdate, remove } = useSWRCrud<Fulfillment>(
    `/api/degree/degreeplans/${degreeID}/fulfillments`,
    {
      idKey: "full_code",
      createDefaultOptimisticData: { semester: null, rules: [] },
    }
  );

  // Workaround solution to only input courses once degree has been created and degreeID exists.
  // Will likely change in the future!
  useEffect(() => {
    if (degreeID) {
      console.log(degreeID)

      for (let sem of scrapedCourses) {
        console.log(sem)
        let semCode = ""
        if (sem.sem == "_TRAN") semCode = sem.sem

        else {
          semCode = sem.sem.match(/(\d+)/)[0];
          if (sem.sem.includes("spring")) semCode += "A";
          else if (sem.sem.includes("summer")) semCode += "B";
          else semCode += "C";
        }

        for (let course of sem.courses) {
          let code = course.replace(" ", "-").toUpperCase();
          createOrUpdate({ semester: semCode }, code);
        }
      }

      setShowOnboardingModal(false);
      // location.reload();
    }
  }, [degreeID]);

  const complete =
    startingYear !== null &&
    graduationYear !== null &&
    schools.length > 0 &&
    majors.length > 0 &&
    name !== "";

  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);

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
    const majorOptions = degrees
      ?.filter((d) => schools.map((s) => s.value).includes(d.degree))
      .sort((d) =>
        Math.abs((startingYear ? startingYear.value : d.year) - d.year)
      )
      .map((degree) => ({
        value: degree,
        label: createMajorLabel(degree),
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
    return majorOptions;
  }, [schools, startingYear]);

  const handleAddDegrees = () => {
    createDegreeplan({ name: name }).then((res) => {
      if (res) {
        if (startingYear && graduationYear) {
          const semesters = interpolateSemesters(
            startingYear.value,
            graduationYear.value
          );
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

        setDegreeID(res.id);
      }
    });
  };

  // TRANSCRIPT PARSING
  const total = useRef<any>({})

  const addText = (items: (any)[], index: number) => {
    console.log(items, index)
    let allText: any = { "col0": [], "col1": [] }
    let maxCol = items.reduce(function (acc, el) {
      if (el.str === '_________________________________________________________________') {
        return Math.max(el.transform[4], acc)
      }
      return acc
    }, -100)
    // console.log(maxCol)

    for (let i in items) {
      let col = items[i]?.transform[4];
      let pos = items[i]?.transform[5];

      let currentCol = col < maxCol ? "col0" : "col1";

      if (items[i].str === "Level:High School") {
        allText[currentCol] = [];
        break
      }

      if (pos in allText[currentCol])
        allText[currentCol][pos].push(items[i]?.str);
      else
        allText[currentCol][pos] = [items[i]?.str];
    }

    let textResult = [];
    for (let col in allText) {
      let poses = Object.keys(allText[col]).reverse();

      for (let i in poses) {
        textResult.push(allText[col][poses[i]].join("").toLowerCase());
      }
      total.current[index] = textResult;
      console.log(total.current)
      console.log("**********")
    }


    console.log(Object.keys(total.current).length)
    if (Object.keys(total.current).length === numPages) {

      let all: any = []
      console.log(Object.keys(total.current).sort())
      for (let key in Object.keys(total.current).sort()) {
        all = all.concat(total.current[key])
      }

      parseTranscript(all)
    }
  }

  const parseTranscript = (textResult: any) => {

    let separatedCourses: any = [];

    for (let l in textResult) {
      // SCRAPE SCHOOL
      if (textResult[l].includes("program")) {
        let program = textResult[l].replace(/^.*?:\s*/, "");
        let tempSchools = [];
        if (program.includes("arts"))
          tempSchools.push({ value: "BA", label: "Arts & Sciences" });
        // TODO: Ensure these are right!
        if (program.includes("school of engineering and applied science")) {
          if (textResult[parseInt(l)+1].includes("bachelor of science in engineering"))
            tempSchools.push({ value: "BSE", label: "Engineering BSE" });
          else
            tempSchools.push({ value: "BAS", label: "Engineering BAS" });
        }
      
        if (program.includes("wharton"))
          tempSchools.push({ value: "BS", label: "Wharton" });
        if (program.includes("nursing"))
          tempSchools.push({ value: "BSN", label: "Nursing" });
        setSchools(tempSchools);
      }

      // SCRAPE MAJOR
      if (textResult[l].includes("major")) {
        let major = textResult[l].replace(/^.*?:\s*/, "");
        console.log(major);
      }

      // Regex gets an array for total institution values -> [Earned Hours, GPA Hours, Points, GPA]
      if (textResult[l].includes("total institution")) {
        let totalNums = textResult[l].match(/\d+\.\d+/g);
        if (totalNums) {
          let credit_hours = totalNums[0];
          let gpa = totalNums[3];
          console.log(credit_hours);
          console.log(gpa);
        }
      }

      // Regex gets array for total transfer values -> [Earned Hours]
      if (textResult[l].includes("total transfer")) {
        let totalNums = textResult[l].match(/\d+\.\d+/g);
        if (totalNums) {
          let transfer_hours = totalNums[0];
          console.log(transfer_hours);
        }
      }


      // SCRAPE AP AND TRANSFER CREDIT
      if (textResult[l].includes("transfer credit")) {
        let truncatedTranscript = textResult.slice(parseInt(l) + 1);
        let courses = [];
        for (let line of truncatedTranscript) {
          // Match lines following course code format
          let courseMatch = line.match(/\b\w+\s\d{3,4}\b/); 
          if (
            courseMatch &&
            // Match lines following [term] [year] format
            !/(fall|spring|summer)\s\d{4}/i.test(courseMatch)
          ) {
            courses.push(courseMatch[0]);
          } else if (line.includes("institution credit")) {
            separatedCourses["_TRAN"] = courses;
            console.log(courses);
            break;
          }
        }
      }

      // SCRAPE COURSES (BY SEM)
      if (textResult[l].includes("institution credit")) {
        let truncatedTranscript = textResult.slice(parseInt(l) + 1);
        let currentSem = "";
        for (let line of truncatedTranscript) {
          if (/(fall|spring|summer)\s\d{4}/i.test(line)) {
            currentSem = line;
            separatedCourses[currentSem] = [];
          } else {
            let courseMatch = line.match(/\b\w+\s\d{3,4}\b/);
            if (courseMatch) {
              separatedCourses[currentSem].push(courseMatch[0]);
            }
          }
        }
        separatedCourses = Object.keys(separatedCourses).map(
          (key) => [{ sem: key, courses: separatedCourses[key] }][0]
        );
        console.log(separatedCourses);

        setScrapedCourses(separatedCourses);

        // SCRAPE START YEAR AND INFER GRAD YEAR
        let years = separatedCourses.map((e, i) => {
              return parseInt(e.sem.replace(/\D/g, ""));
        });
        years.shift()
        let startYear = Math.min(...years);
        setStartingYear({
          value: startYear,
          label: startYear,
        });
        setGraduationYear({
          value: startYear + 4,
          label: startYear + 4,
        });
      }
    }
  };

  if (currentPage === 0)
    return (
      <CenteredFlexContainer>
        <ChooseContainer $maxWidth="90%" $minWidth="90%">
          <h1>Welcome to Penn Degree Plan!</h1>
          <label>
            <input
              type="file"
              accept=".pdf"
              hidden
              onChange={(event) => {
                if (event.target.files) setPDF(event.target.files[0]);
              }}
            />
            <Upload>
              <p style={{ fontSize: "1.2rem" }}>Upload Transcript</p>
              {PDF?.name ? (
                <p>{PDF?.name}</p>
              ) : (
                <UploadIcon width={20} height={20} />
              )}
            </Upload>
          </label>
          <NextButton
            onClick={() => {
              setCurrentPage(1);
            }}
            disabled={PDF ? false : true}
            style={{
              height: "45px",
              width: "100px",
              borderRadius: "7px",
              color: PDF ? "white" : "",
              transition: "all 0.25s",
            }}
          >
            Next
          </NextButton>
          <TextButton
            onClick={() => {
              setCurrentPage(2);
            }}
            style={{ borderBottom: "1px solid #aaa" }}
          >
            <p>Enter information manually</p>
            <ArrowRightIcon />
          </TextButton>
        </ChooseContainer>
      </CenteredFlexContainer>
    );

  if (currentPage === 1)
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
                  onChange={(selectedOption) =>
                    setGraduationYear(selectedOption)
                  }
                  isClearable
                  placeholder="Select Year of Graduation"
                  styles={customSelectStylesLeft}
                />
              </FieldWrapper>

              <FieldWrapper>
                <Label required>School(s) or Program(s)</Label>
                <Select
                  options={schoolOptions}
                  value={schools}
                  onChange={(selectedOptions) =>
                    setSchools([...selectedOptions])
                  }
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
                  onChange={(selectedOptions) =>
                    setMajors([...selectedOptions])
                  }
                  isClearable
                  isMulti
                  isDisabled={schools.length === 0}
                  placeholder={"Major - Concentration"}
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

              <div style={{ display: "none" }}>
                <Document
                  file={PDF}
                  onLoadSuccess={(pdf) => {
                    setNumPages(pdf.numPages);
                  }}
                >
                  {Array.from(new Array(numPages), (el, index) => (
                    <Page
                      key={`page_${index + 1}`}
                      pageNumber={index + 1}
                      onGetTextSuccess={({ items, styles }) =>
                        addText(items, index)
                      }
                      renderTextLayer={true}
                    />
                  ))}
                </Document>
              </div>
            </Column>

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
              {scrapedCourses.map((e, i) => {
                const semCourses = e.courses.map(
                  (course, _) =>
                    [
                      {
                        value: course.toUpperCase(),
                        label: course.toUpperCase(),
                      },
                    ][0]
                );
                return (
                  <FieldWrapper style={{ display: "flex" }}>
                    { e.sem === "_TRAN" 
                      ? <Label required={false}>Transfer Credit</Label>
                      : <Label required={false}>{e.sem[0].toUpperCase() + e.sem.slice(1)}</Label>
                    }
                    <Select
                      components={{ MultiValueRemove: () => null }}
                      options={semCourses}
                      value={semCourses}
                      // onChange={(selectedOptions) => console.log(selectedOptions)}
                      // isClearable
                      isMulti
                      placeholder="Courses"
                      styles={customSelectStylesCourses}
                      isLoading={isLoadingDegrees}
                      isDisabled
                    />
                  </FieldWrapper>
                );
              })}
              <NextButtonContainer>
                <NextButton
                  onClick={handleAddDegrees}
                  disabled={!complete}
                  style={{
                    height: "35px",
                    width: "90px",
                    borderRadius: "7px",
                    color: PDF ? "white" : "",
                    transition: "all 0.25s",
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

  if (currentPage === 2)
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
          <h1 style={{ paddingLeft: "5%", paddingTop: "1.25%" }}>
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
                  onChange={(selectedOption) =>
                    setGraduationYear(selectedOption)
                  }
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
                  onChange={(selectedOptions) =>
                    setSchools([...selectedOptions])
                  }
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
                  onChange={(selectedOptions) =>
                    setMajors([...selectedOptions])
                  }
                  isClearable
                  isMulti
                  isDisabled={schools.length === 0}
                  placeholder={"Major - Concentration"}
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
              <div style={{ display: "none" }}>
                <Document
                  file={PDF}
                  onLoadSuccess={(pdf) => {
                    setNumPages(pdf.numPages);
                  }}
                >
                  {Array.from(new Array(numPages), (el, index) => (
                    <Page
                      key={`page_${index + 1}`}
                      pageNumber={index + 1}
                      onGetTextSuccess={({ items, styles }) =>
                        handleTranscript(items)
                      }
                      renderTextLayer={true}
                    />
                  ))}
                </Document>
              </div>
            </Column>
          </ColumnsContainer>
        </PanelContainer>
      </CenteredFlexContainer>
    );
};

export default OnboardingPage;
