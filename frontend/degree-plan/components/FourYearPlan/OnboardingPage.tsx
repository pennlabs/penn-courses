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
  Degree,
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
import { polyfillPromiseWithResolvers } from "../../pages/polyfilsResolver";

import "core-js/full/promise/with-resolvers.js";
import {
  UploadIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  RulerSquareIcon,
} from "@radix-ui/react-icons";
import { PulseLoader } from "react-spinners";
polyfillPromiseWithResolvers();


const { closest } = require('fastest-levenshtein');

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.mjs`;

const PanelContainer = styled.div<{ $maxWidth: string; $minWidth: string }>`
  border-radius: 10px;
  box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
  background-color: #ffffff;
  margin: 1rem;
  min-height: 85%;
  // overflow: hidden; /* Hide scrollbars */
  width: ${(props) => (props.$maxWidth || props.$maxWidth ? "auto" : "100%")};
  max-width: ${(props) => (props.$maxWidth ? props.$maxWidth : "auto")};
  min-width: ${(props) => (props.$minWidth ? props.$minWidth : "auto")};
  position: relative;
  padding-bottom: "5%";
  z-index: 100000;
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
  gap: 40px;
`;

const ContainerGroup = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
`

const ErrorText = styled.p`
  color: darkred;
  min-height: 17px;
`

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
  padding-right: 5%;
  gap: 20px;
  min-height: 100%;
  padding-bottom: 5%;

  @media (max-width: 768px) {
    flex-direction: column;
    padding-bottom: 5%;
  }
`;

const CourseContainer = styled.div`
  max-height: 48vh;
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
  padding-right: 2%;
  padding-bottom: 2rem;

  
  // Scroll shadow credits: https://css-tricks.com/books/greatest-css-tricks/scroll-shadows/

  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overflow-scrolling: touch;

  background:
    /* Shadow Cover TOP */
    linear-gradient(
      white 30%,
      rgba(255, 255, 255, 0)
    ) center top,
    
    /* Shadow Cover BOTTOM */
    linear-gradient(
      rgba(255, 255, 255, 0), 
      white 70%
    ) center bottom,
    
    /* Shadow TOP */
    radial-gradient(
      farthest-side at 50% 0,
      rgba(0, 0, 0, 0.4),
      rgba(0, 0, 0, 0)
    ) center top,
    
    /* Shadow BOTTOM */
    radial-gradient(
      farthest-side at 50% 100%,
      rgba(0, 0, 0, 0.3),
      rgba(0, 0, 0, 0)
    ) center bottom;
  
  background-repeat: no-repeat;
  background-size: 100% 40px, 100% 40px, 100% 14px, 100% 14px;
  background-attachment: local, local, scroll, scroll;

  // &::-webkit-scrollbar {
  //     background-color: transparent;
  //     width: 7px;

  // }

  // &::-webkit-scrollbar-thumb {
  //   background-color: lightgray;
  //   border-radius: 10px;
  // }
}

`

export const Column = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
`;

const NextButtonContainer = styled.div`
  padding-top: 5%;
  // padding-right: 15%;
  display: flex;
  flex-direction: row;
  justify-content: end;

  @media (max-width: 768px) {
    padding-right: 5%;
    width: 100%;
    justify-content: center;
  }
`;

const NextButton = styled(Button) <{ disabled: boolean }>`
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
  { value: "MSE", label: "Engineering AM"}
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

const ScrollableCol = styled.div`
  display: flex;

`

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
    // maxWidth: "90px",
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
    width: "100%",
    minHeight: "35px",
    // height: "65px",
    zIndex: -1

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
    zIndex: -1
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

  const [degreeID, setDegreeID] = useState<number | null>(null);
  const [coursesToRules, setCoursesToRules] = useState<any>(null);

  const [loading, setLoading] = useState(false);

  const { create: createDegreeplan } = useSWRCrud<DegreePlan>(
    "/api/degree/degreeplans"
  );


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
    if (degreeID && coursesToRules) {
      let allCodes = "";
      for (let sem of scrapedCourses) {
        if (sem.courses.length > 0) {
          let semCode = ""
          if (sem.sem == "_TRAN") semCode = "TRAN"
          else {
            semCode = sem.sem.match(/(\d+)/)[0];
            if (sem.sem.includes("spring")) semCode += "A";
            else if (sem.sem.includes("summer")) semCode += "B";
            else semCode += "C";
          }
          allCodes += sem.courses.reduce((acc: String, course: String) => {
            return acc + course.replace(" ", "-").toUpperCase() + "_" + semCode + ","
          }, "")
        }
      }
      
      if (allCodes == "") {
        setShowOnboardingModal(false);
      } else {
        allCodes = allCodes.slice(0, -1)
        fetch(`/api/degree/onboard-from-transcript/${degreeID}/${allCodes}`).then((r) => {
          r.json().then((data) => {
            setShowOnboardingModal(false);
          })
        })
      }
    }
  }, [degreeID, coursesToRules]);

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


  const getMajorOptions = (degrees: DegreeListing[] | undefined, schools: SchoolOption[], startingYear: any) => {
    const majorOptions = degrees
      ?.filter((d) => schools.map((s) => s.value).includes(d.degree))
      .sort((d) =>
        Math.abs((startingYear ? startingYear : d.year) - d.year)
      )
      .map((degree) => ({
        value: degree,
        label: createMajorLabel(degree),
      }))
      .sort((a, b) => a.label.localeCompare(b.label));
    return majorOptions;
  }

  const majorOptionsCallback = React.useCallback(() => {
    const majorOptions = getMajorOptions(degrees, schools, startingYear);
    return majorOptions;
  }, [schools, startingYear]);

  const handleAddDegrees = () => {
    setLoading(true);
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
        ).then((res) => {
          // Compile courses that are explicitly listed under a certain rule (Ex. CIS-1200)     
          let coursesToRules: any = {}

          // Recursively find all courses explicitly listed and pairs each with their rule #
          // TO DO: add support for things like WRIT 0000-5999 (given range of valid courses)  
          function findFinalRulesOrQJson(obj: any) {
            // If q_json has type COURSE, add the single listed course to coursesToRules
            if (obj?.q_json?.type === "COURSE") {
              coursesToRules[obj.q_json.full_code] = obj.id;
            }

            // If q_json has type OR, add all listed courses to coursesToRules
            else if (obj?.q_json?.type === "OR") {
              for (let course of obj.q_json.clauses) {
                if (course.type === "COURSE") {
                  coursesToRules[course.full_code] = obj.id;
                }
              }
            }

            // Else, loop through all rules
            if (obj?.rules && obj?.rules.length != 0) {
              for (let rule of obj.rules) {
                findFinalRulesOrQJson(rule)
              }
            }
          }

          for (let degree of res.degrees) {
            findFinalRulesOrQJson(degree)
          }

          setCoursesToRules(coursesToRules);
        }); // add degree
        setActiveDegreeplan(res);
        setDegreeID(res.id);
      }
    });
  };


  // TRANSCRIPT PARSING
  const total = useRef<any>({});

  const addText = (items: (any)[], index: number) => {
    // At most the transcript will have two columns - we account for that here.
    let allText: any = { "col0": [], "col1": [] }

    // Find x value for when second column begins using convenient lines.
    let maxCol = items.reduce(function (acc, el) {
      if (el.str === '_________________________________________________________________') {
        return Math.max(el.transform[4], acc)
      }
      return acc
    }, -100)

    for (let i in items) {
      let col = items[i]?.transform[4];
      let pos = items[i]?.transform[5];

      let currentCol = col < maxCol ? "col0" : "col1";

      // Ignore potential high school program transcript
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
    }

    // If all pages have been read, begin to parse text from transcript
    if (Object.keys(total.current).length === numPages) {
      let all: any = []
      for (let key in Object.keys(total.current).sort()) {
        all = all.concat(total.current[key])
      }
      parseTranscript(all)
    }
  }

  const transcriptDetected = useRef<boolean | null>(null);

  const parseTranscript = (textResult: any) => {
    let separatedCourses: any = [];

    let startYear: number = 0;
    let tempSchools: any = [];
    let detectedMajors: string[] = [];
    let detectedConcentrations: string[] = [];

    for (let l in textResult) {
      // SCRAPE SCHOOL
      if (textResult[l].replaceAll(" ", "").includes("program:")) {
        let program = textResult[l].replace(/^.*?:\s*/, "");
        if (program.includes("arts"))
          tempSchools.push({ value: "BA", label: "Arts & Sciences" });

        if (program.includes("school of engineering and applied science")) {
          if (textResult[parseInt(l) + 1].includes("bachelor of science in engineering"))
            tempSchools.push({ value: "BSE", label: "Engineering BSE" });
          else
            tempSchools.push({ value: "BAS", label: "Engineering BAS" });
        }

        // TODO: Ensure these are right!
        if (program.includes("wharton"))
          tempSchools.push({ value: "BS", label: "Wharton" });
        if (program.includes("nursing"))
          tempSchools.push({ value: "BSN", label: "Nursing" });
        if (tempSchools.length)
          setSchools(tempSchools);
      }

      // SCRAPE MAJOR
      if (textResult[l].includes("major")) {
        detectedMajors.push(textResult[l].replace(/^.*?:\s*/, ""));
      }

      // SCRAPE CONCENTRATION
      if (textResult[l].includes("concentration")) {
        detectedConcentrations.push(textResult[l].replace(/^.*?:\s*/, ""));
      }

      // Regex gets an array for total institution values -> [Earned Hours, GPA Hours, Points, GPA]
      if (textResult[l].includes("total institution")) {
        let totalNums = textResult[l].match(/\d+\.\d+/g);
        if (totalNums) {
          let credit_hours = totalNums[0];
          let gpa = totalNums[3];
        }
      }

      // Regex gets array for total transfer values -> [Earned Hours]
      if (textResult[l].includes("total transfer")) {
        let totalNums = textResult[l].match(/\d+\.\d+/g);
        if (totalNums) {
          let transfer_hours = totalNums[0];
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
              // Check if course didn't get an F or a W. If current sem's courses are empty, remove sem key from separatedCourses
              if ((line[line.length - 1] == "f" || line[line.length - 1] == "w") && separatedCourses[currentSem].length == 0) {
                delete separatedCourses[currentSem];
              }
              else {
                separatedCourses[currentSem].push(courseMatch[0]);
              }
            }
          }
        }
        separatedCourses = Object.keys(separatedCourses).map(
          (key) => [{ sem: key, courses: separatedCourses[key] }][0]
        );

        setScrapedCourses(separatedCourses);

        // SCRAPE START YEAR AND INFER GRAD YEAR
        let years = separatedCourses.map((e: any, i: number) => {
          return parseInt(e.sem.replace(/\D/g, ""));
        });
        years.shift()
        startYear = Math.min(...years);
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

    // Match majors
    let detectedMajorsOptions = [];

    let possibleDegrees = getMajorOptions(degrees, tempSchools, startYear)
    for (let i in detectedMajors) {
      let m = detectedMajors[i] + (detectedConcentrations.length > parseInt(i) ? detectedConcentrations[i] : "")
      if (!detectedMajors[i]?.includes("undeclared") && possibleDegrees) {
        let justMajorNames = possibleDegrees.reduce((acc: any, el: any) => {
          acc.push(el.label);
          return acc;
        }, [])

        let closestMajor = m == "computer science " ? "Computer Science - No Concentration (2024)" : closest(m, justMajorNames)
        var majorOption = possibleDegrees.find(obj => {
          return obj.label === closestMajor
        })
        if (majorOption) detectedMajorsOptions.push(majorOption)
      }
    }
    setMajors(detectedMajorsOptions)


    transcriptDetected.current = startYear ? true : false;
  };


  const resetParser = () => {
    total.current = {};
    transcriptDetected.current = null;
    setSchools([]);
    setMajors([]);
    setMinor([]);
    setName("");
    setScrapedCourses([]);
    setStartingYear(null);
    setGraduationYear(null);
  }

  if (currentPage === 0)
    return (
      <CenteredFlexContainer>
        <ChooseContainer $maxWidth="90%" $minWidth="90%">
          <div style={{ display: "none" }}>
            <Document
              file={PDF}
              onLoadSuccess={(pdf) => {
                resetParser();
                setNumPages(pdf.numPages);
              }}
            >
              {Array.from(new Array(numPages), (el, index) => (
                <Page
                  key={`page_${index + 1}`}
                  pageNumber={index + 1}
                  onGetTextSuccess={({ items, styles }) => {
                    addText(items, index);
                  }
                  }
                  renderTextLayer={true}
                />
              ))}
            </Document>
          </div>

          <h1>Welcome to Penn Degree Plan!</h1>
          <ContainerGroup>
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
            <ErrorText>{PDF && transcriptDetected.current !== null && (transcriptDetected.current === true ? "" : "Can't detect a transcript! Try another file.")}</ErrorText>
            <NextButton
              onClick={() => {
                if (startingYear && startingYear?.value !== 0)
                  setCurrentPage(1);
              }}
              disabled={PDF && transcriptDetected.current === true ? false : true}
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
          </ContainerGroup>
          <TextButton
            onClick={() => {
              resetParser();
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
                  options={majorOptionsCallback()}
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

              {/* <div style={{ display: "none" }}>
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
              </div> */}
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

              {/* <CourseContainer style={{ width: "85%" }}> */}
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
                      {e.sem === "_TRAN"
                        ? <Label required={false}>Transfer Credit</Label>
                        : <Label required={false}>{e.sem[0].toUpperCase() + e.sem.slice(1)}</Label>
                      }
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
                    color: PDF ? "white" : "",
                    transition: "all 0.25s",
                  }}
                >
                  {!loading && <div>Next</div>}
                  <PulseLoader 
                    size={8}
                    color={"white"}
                    loading={loading}
                  />
                </NextButton>
              </NextButtonContainer>
            </Column>
          </ColumnsContainer>
        </PanelContainer>
      </CenteredFlexContainer>
    );

  return (
    <CenteredFlexContainer>
      <PanelContainer $maxWidth="90%" $minWidth="90%">
        <TextButton
          onClick={() => {
            setCurrentPage(0);
            setSchools([]);
            setMajors([]);
            setMinor([]);
            setName("");
            setScrapedCourses([]);
            setStartingYear(null);
            setGraduationYear(null);
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
                options={majorOptionsCallback()}
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
          </Column>
        </ColumnsContainer>
      </PanelContainer>
    </CenteredFlexContainer>
  );
};

export default OnboardingPage;
