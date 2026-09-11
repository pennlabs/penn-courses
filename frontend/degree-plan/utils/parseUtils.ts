import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { DegreeListing, Major, SchoolOption } from "@/types";
const { distance } = require("fastest-levenshtein");

// How far a transcript's wording may sit from a program's name and still be the same thing.
const matchTolerance = (name: string) => Math.max(3, Math.floor(name.length / 3));

const normalize = (text: string) => text.toLowerCase().replace(/\s+/g, " ").trim();

// What a program calls its own absence of a concentration, for transcripts that name none.
const NO_CONCENTRATION = new Set(["", "no concentration", "general", "none"]);

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

export type MajorOptionItem = {
  value: Major;
  label: string;
};

// Majors that can be added on top of a degree. Deliberately not filtered by school. e.g. a student
// in Engineering may add the major part of a College degree, which is what a second major is.
export const getSecondMajorOptions = (
  majors: Major[] | undefined,
  startingYear: number | null
): MajorOptionItem[] | undefined =>
  majors
    ?.slice()
    .sort((a, b) => Math.abs((startingYear || a.year) - a.year) - Math.abs((startingYear || b.year) - b.year))
    .map((major) => ({
      value: major,
      label: major.concentration_name
        ? `${major.name} - ${major.concentration_name} (${major.year})`
        : `${major.name} (${major.year})`,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

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

// Returns the option whose program name is closest to the transcript's wording, or undefined
// if no option is close enough. 
const matchOption = <T>(
  major: string,
  concentration: string,
  options: T[] | undefined,
  namesOf: (option: T) => [string, string]
): T | undefined => {
  if (!options?.length) return undefined;

  const target = normalize(major);
  const scored = options.map((option) => {
    const [name, optionConcentration] = namesOf(option);
    return {
      option,
      name: normalize(name ?? ""),
      concentration: normalize(optionConcentration ?? ""),
      distance: distance(target, normalize(name ?? "")),
    };
  });

  const best = Math.min(...scored.map((candidate) => candidate.distance));
  const closest = scored.filter((candidate) => candidate.distance === best);
  if (best > matchTolerance(closest[0].name)) return undefined;

  const wanted = normalize(concentration);
  const preferred = wanted
    ? closest.find(
        (candidate) =>
          candidate.concentration &&
          distance(wanted, candidate.concentration) <= matchTolerance(candidate.concentration)
      )
    : closest.find((candidate) => NO_CONCENTRATION.has(candidate.concentration));

  return (preferred ?? closest[0]).option;
};

// Given the majors and concentrations read off a transcript, work out which are degrees the
// student is enrolled in and which are majors added on top of one.
//
// A transcript names every major without saying which is which, so each is matched against the
// degrees of the schools detected first, and against the standalone majors only if that fails.
export const detectMajors = (
  detectedMajors: string[],
  detectedConcentrations: string[],
  possibleDegrees: DegreeOption[] | undefined,
  possibleMajors: MajorOptionItem[] | undefined
) => {
  const degreeOptions: DegreeOption[] = [];
  const majorOptions: MajorOptionItem[] = [];

  detectedMajors.forEach((major, i) => {
    if (!major || major.includes("undeclared")) return;
    const concentration = detectedConcentrations[i] ?? "";

    const degree = matchOption(major, concentration, possibleDegrees, (option) => [
      option.value.major_name,
      option.value.concentration_name,
    ]);
    if (degree) {
      degreeOptions.push(degree);
      return;
    }

    const standalone = matchOption(major, concentration, possibleMajors, (option) => [
      option.value.name ?? "",
      option.value.concentration_name ?? "",
    ]);
    if (standalone) majorOptions.push(standalone);
  });

  return { degreeOptions, majorOptions };
};

// Given a list of lines from the PDF and a list of possible degrees,
// return a scraped information.
export const parseTranscript = (
  textResult: string[],
  degrees: DegreeListing[] | undefined,
  majors: Major[] | undefined
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

  const formattedSeparatedCourses = Object.values(
    Object.entries(courseToSem).reduce(
      (acc, [course, sem]) => {
        const trimmedSem = sem.trim();
        if (!acc[trimmedSem]) acc[trimmedSem] = { sem: trimmedSem, courses: [] };
        acc[trimmedSem].courses.push(course);
        return acc;
      },
      {} as { [key: string]: { sem: string; courses: string[] } }
    )
  );

  // Scrape start year and infer grad year (skip _TRAN which yields NaN)
  const years = formattedSeparatedCourses
    .map(({ sem }) => parseInt(sem.replace(/\D/g, "")))
    .filter((y) => !isNaN(y));
  startYear = years.length ? Math.min(...years) : 0;

  const possibleDegrees = getMajorOptions(degrees, tempSchools, startYear);
  const { degreeOptions, majorOptions } = detectMajors(
    detectedMajors,
    detectedConcentrations,
    possibleDegrees,
    getSecondMajorOptions(majors, startYear)
  );

  return {
    scrapedCourses: formattedSeparatedCourses,
    startYear: startYear,
    scrapedSchools: tempSchools,
    detectedMajorsOptions: degreeOptions,
    detectedSecondMajorOptions: majorOptions,
  };
};
