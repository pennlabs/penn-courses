import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { DegreeListing, SchoolOption } from "@/types";
const { closest } = require("fastest-levenshtein");

type LineItem = {
  dir: string;
  fontName: string;
  hasEOL: boolean;
  height: number;
  str: string;
  transform: number[];
  width: number;
};

type DegreeOption = {
  value: DegreeListing;
  label: string;
};

type ParsedTextColumn = Record<string, string[]>;

export type ParsedText = {
  col0: ParsedTextColumn;
  col1: ParsedTextColumn;
};

// Given a parsed text object, return a flattened array of strings.
export const flattenParsedText = (parsedText: ParsedText): string[] => {
  const columns: (keyof ParsedText)[] = ["col0", "col1"];
  const flattened: string[] = [];

  columns.forEach((column) => {
    const columnRows = parsedText[column];
    const poses = Object.keys(columnRows).reverse();
    poses.forEach((pose) => {
      const row = columnRows[pose];
      flattened.push(row.join("").toLowerCase());
    });
  });

  return flattened;
};


// Given a list of line items from the PDF, return an object of columns and the lines in each column.
export const parseItems = (items: LineItem[]) => {
  // At most the transcript will have two columns - we account for that here.
  let allText: ParsedText = { col0: {}, col1: {} };

  // Find x value for when second column begins using convenient lines.
  let maxCol = items.reduce(function (acc, el) {
    if (
      el.str ===
      "_________________________________________________________________"
    ) {
      return Math.max(el.transform[4], acc);
    }
    return acc;
  }, -100);

  for (let i in items) {
    let col = items[i]?.transform[4];
    let pos = items[i]?.transform[5];

    let currentCol: "col0" | "col1" = col < maxCol ? "col0" : "col1";

    // Ignore potential high school program transcript
    if (items[i].str === "Level:High School") {
      allText[currentCol] = {};
      break;
    }
    if (pos in allText[currentCol])
      allText[currentCol][pos].push(items[i]?.str);
    else allText[currentCol][pos] = [items[i]?.str];
  }

  return allText;
};

// Given a list of degrees, a list of schools, and a starting year,
// return a list of relevant possible majors.
export const getMajorOptions = (
  degrees: DegreeListing[] | undefined,
  schools: SchoolOption[],
  startingYear: number | null
): DegreeOption[] | undefined => {
  const majorOptions = degrees
    ?.filter((d) => schools.map((s) => s.value).includes(d.degree))
    .sort((d) => Math.abs((startingYear ? startingYear : d.year) - d.year))
    .map((degree) => ({
      value: degree,
      label: createMajorLabel(degree),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
  return majorOptions;
};

// Given a string[] where we're guaranteed to have a school line, return a list of scraped schools.
const checkSchool = (textResult: string[], l: number) => {
  const tempSchools = [];
  let program = textResult[l].replace(/^.*?:\s*/, "");
  if (program.includes("arts"))
    tempSchools.push({ value: "BA", label: "Arts & Sciences" });
  if (program.includes("school of engineering and applied science")) {
    if (textResult[l + 1].includes("bachelor of science in engineering"))
      tempSchools.push({ value: "BSE", label: "Engineering BSE" });
    else tempSchools.push({ value: "BAS", label: "Engineering BAS" });
  }
  if (program.includes("wharton"))
    tempSchools.push({ value: "BS", label: "Wharton" });
  if (program.includes("nursing"))
    tempSchools.push({ value: "BSN", label: "Nursing" });

  return tempSchools;
};

// Given a string[] where we're guaranteed to have a transfer credit line,
// return a list of scraped AP and transfer courses. Stops when we reach potentially
// non-transfer credit lines.
const getAPAndTransferCourses = (textResult: any, l: number) => {
  let courses: { [key: string]: string } = {};
  let truncatedTranscript = textResult.slice(l + 1);
  for (let line of truncatedTranscript) {
    // Match lines following course code format
    let courseMatch = line.match(/\b\w+\s\d{3,4}\b/);
    if (
      courseMatch &&
      // Match lines following [term] [year] format
      !/(fall|spring|summer)\s\d{4}/i.test(courseMatch)
    ) {
      courses[courseMatch[0]] = "_TRAN";
    } else if (line.includes("institution credit")) {
      break;
    }
  }
  return courses;
};

// Given a string[] where what follows is guaranteed to be the student's non-transfer courses,
// return an array of semester + courses objects.
const getCourseToSem = (truncatedTranscript: string[]) => {
  let firstNonSummerSemReached = false;
  let currentSem = "";
  let courseToSem: { [key: string]: string } = {};
  for (let line of truncatedTranscript) {
    if (/(fall|spring|summer)\s\d{4}/i.test(line)) {
      currentSem = line;
      if (!firstNonSummerSemReached && !currentSem.includes("summer")) {
        firstNonSummerSemReached = true;
      }
    } else {
      let courseMatch = line.match(/\b[A-Za-z]{2,}\s\d{3,4}\b/);
      if (courseMatch) {
        // Check if course didn't get an F or a W. If so, add to current sem or _TRAN
        if (!(line[line.length - 1] == "f" || line[line.length - 1] == "w")) {
          // TODO: We don't yet have a way to track courses that can be taken multiple times,
          // so we store a course that appears multiple times only in the most recent semester it appears in.
          if (courseMatch[0] in courseToSem) {
            courseToSem[courseMatch[0]] = currentSem;
          } else {
            // Add all pre-college courses to _TRAN semester
            if (firstNonSummerSemReached) {
              courseToSem[courseMatch[0]] = currentSem;
            } else {
              courseToSem[courseMatch[0]] = "_TRAN";
            }
          }
        }
      }
    }
  }
  return courseToSem;
};

// Given a list of detected majors, a list of detected concentrations, and a list of possible degrees,
// return a list of detected majors options.
const detectMajors = (
  detectedMajors: string[],
  detectedConcentrations: string[],
  possibleDegrees: DegreeOption[] | undefined
) => {
  const detectedMajorsOptions = [];
  for (let i in detectedMajors) {
    let m =
      detectedMajors[i] +
      (detectedConcentrations.length > parseInt(i)
        ? detectedConcentrations[i]
        : "");
    if (!detectedMajors[i]?.includes("undeclared") && possibleDegrees) {
      let justMajorNames = possibleDegrees.reduce((acc: any, el: any) => {
        acc.push(el.label);
        return acc;
      }, []);

      let closestMajor =
        m == "computer science "
          ? "Computer Science - No Concentration (2024)"
          : closest(m, justMajorNames);
      var majorOption = possibleDegrees.find((obj) => {
        return obj.label === closestMajor;
      });
      if (majorOption) detectedMajorsOptions.push(majorOption);
    }
  }

  return detectedMajorsOptions;
};

// Given a list of lines from the PDF and a list of possible degrees,
// return a scraped information.
export const parseTranscript = (
  textResult: string[],
  degrees: DegreeListing[] | undefined
) => {
  let courseToSem: { [key: string]: string } = {};
  let startYear: number = 0;
  let tempSchools: { value: string; label: string }[] = [];
  let detectedMajors: string[] = [];
  let detectedConcentrations: string[] = [];

  for (let l = 0; l < textResult.length; l++) {
    if (textResult[l].replaceAll(" ", "").includes("program:")) {
      tempSchools = tempSchools.concat(checkSchool(textResult, l));
    }

    if (textResult[l].includes("major")) {
      detectedMajors.push(textResult[l].replace(/^.*?:\s*/, ""));
    }

    if (textResult[l].includes("concentration")) {
      detectedConcentrations.push(textResult[l].replace(/^.*?:\s*/, ""));
    }

    if (textResult[l].includes("transfer credit")) {
      courseToSem = {
        ...courseToSem,
        ...getAPAndTransferCourses(textResult, l),
      };
    }

    if (textResult[l].includes("institution credit")) {
      courseToSem = {
        ...courseToSem,
        ...getCourseToSem(textResult.slice(l + 1)),
      };
    }
  }

  const separatedCourses = Object.entries(courseToSem).reduce(
    (acc, [course, sem]) => {
      const trimmedSem = sem.trim();
      if (!acc[trimmedSem]) acc[trimmedSem] = [];
      acc[trimmedSem].push(course);
      return acc;
    },
    {} as { [key: string]: string[] }
  );

  const formattedSeparatedCourses = Object.entries(separatedCourses).map(
    ([sem, courses]) => ({
      sem,
      courses,
    })
  );

  // Scrape start year and infer grad year
  let years = formattedSeparatedCourses.map(
    (e: { sem: string; courses: string[] }, i: number) => {
      return parseInt(e.sem.replace(/\D/g, ""));
    }
  );
  years.shift();
  startYear = Math.min(...years);

  let possibleDegrees = getMajorOptions(degrees, tempSchools, startYear);
  let detectedMajorsOptions = detectMajors(
    detectedMajors,
    detectedConcentrations,
    possibleDegrees
  );

  return {
    scrapedCourses: formattedSeparatedCourses,
    startYear: startYear,
    scrapedSchools: tempSchools,
    detectedMajorsOptions: detectedMajorsOptions,
  };
};
