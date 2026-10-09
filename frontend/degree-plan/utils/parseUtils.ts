import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { schoolOptions } from "@/components/OnboardingPanels/SharedComponents";
import { DegreeListing, Major, SchoolOption } from "@/types";
const { distance } = require("fastest-levenshtein");

// How far a transcript's wording may sit from a program's name and still be the same thing.
const matchTolerance = (name: string) => Math.max(3, Math.floor(name.length / 3));

const normalize = (text: string) => text.toLowerCase().replace(/\s+/g, " ").trim();

// What a program calls its own absence of a concentration, for transcripts that name none.
// Transcripts and the catalog disagree on the wording, so a transcript's "Non Designated" has
// to match a program's "General" or "No Concentration".
const NO_CONCENTRATION = new Set([
  "",
  "no concentration",
  "general",
  "none",
  "non designated",
  "not designated",
]);

type LineItem = {
  dir: string;
  fontName: string;
  hasEOL: boolean;
  height: number;
  str: string;
  transform: number[];
  width: number;
};

export type DegreeOption = {
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

// Given a list of degrees, a school and a starting year, return the primary majors the
// school offers for that starting year. Nothing is offered until a starting year is known,
// since a student is held to the requirements of the year they started.
export const getMajorOptions = (
  degrees: DegreeListing[] | undefined,
  school: SchoolOption | null | undefined,
  startingYear: number | null
): DegreeOption[] | undefined => {
  if (!degrees) return undefined;
  if (!school || !startingYear) return [];
  return degrees
    .filter((d) => d.degree === school.value && d.year === startingYear)
    .map((degree) => ({
      value: degree,
      label: createMajorLabel(degree),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
};

export type MajorOptionItem = {
  value: Major;
  label: string;
};

// A Path program code reads MAJOR-DEGREE[-CONCENTRATION], e.g. CSCI-BA-GEN.
const degreeCodeOf = (programCode: string) => programCode.split("-")[1];

// Given the majors that can be added on top of a degree, a school and a starting year, return
// the additional majors the school offers for that starting year. A major's requirements depend
// on the degree it sits under (CSCI as a College major is not CSCI as an Engineering major), so
// only those under the school's own degree are offered.
export const getAdditionalMajorOptions = (
  majors: Major[] | undefined,
  school: SchoolOption | null | undefined,
  startingYear: number | null
): MajorOptionItem[] | undefined => {
  if (!majors) return undefined;
  if (!school || !startingYear) return [];
  return majors
    .filter(
      (major) =>
        major.year === startingYear &&
        degreeCodeOf(major.program_code) === school.value
    )
    .map((major) => ({
      value: major,
      label: major.concentration_name
        ? `${major.name} - ${major.concentration_name} (${major.year})`
        : `${major.name} (${major.year})`,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
};

// A school, the major the student is enrolled in through it, and the majors they add on top.
export type SchoolSelection = {
  school: SchoolOption;
  primary: DegreeOption | null;
  additional: MajorOptionItem[];
};

// What a transcript says about one program: a school and the majors listed under it, in order.
type ParsedProgram = {
  school: SchoolOption;
  majors: { name: string; concentration: string }[];
};

// Given the lines from where a program is named, return the school it belongs to. The program
// line, and the lines up to its division line, are read together because the degree's name can
// wrap onto the following line, or be interleaved with a neighboring column.
const detectSchool = (text: string): SchoolOption | undefined => {
  let value: string | undefined;
  if (text.includes("school of engineering and applied science")) {
    // A submatriculant's masters record names a MSE, which would otherwise fall through to BAS
    // and read as a second bachelors.
    if (text.includes("bachelor of science in engineering")) value = "BSE";
    else if (text.includes("master of science in engineering")) value = "MSE";
    else value = "BAS";
  } else if (text.includes("wharton")) value = "BS";
  else if (text.includes("nursing")) value = "BSN";
  else if (text.includes("arts")) value = "BA";
  return schoolOptions.find((option) => option.value === value);
};

const PROGRAM_LINE = /program\s*:/;

// The text of a program line and the lines that finish naming it.
const programHeader = (textResult: string[], l: number) => {
  const lines = [textResult[l]];
  for (let i = l + 1; i < Math.min(textResult.length, l + 4); i++) {
    if (PROGRAM_LINE.test(textResult[i]) || /\bmajor\s*:/.test(textResult[i])) break;
    lines.push(textResult[i]);
    if (textResult[i].includes("division")) break;
  }
  return lines.join(" ");
};

// The value following "<label> :" on a line. Columns are read side by side, so a line can run
// on into the course listing next to it, which is cut off.
const valueAfter = (line: string, label: string): string | null => {
  const match = line.match(new RegExp(`\\b${label}\\s*:\\s*(.*)$`));
  if (!match) return null;
  return match[1].split(/\s+subj\s+no\.|\s*_{5,}|\s+[a-z]{2,5}\s\d{4}\b/)[0].trim();
};

// Given the lines of a transcript, return each program it lists with the majors under it. A
// major belongs to the closest program above it, and a concentration to the major above it.
export const parsePrograms = (textResult: string[]): ParsedProgram[] => {
  const programs: ParsedProgram[] = [];
  let current: ParsedProgram | undefined;

  for (let l = 0; l < textResult.length; l++) {
    const line = textResult[l];

    if (PROGRAM_LINE.test(line)) {
      const school = detectSchool(programHeader(textResult, l));
      // A program that isn't one of our schools takes its majors with it.
      current = school && { school, majors: [] };
      if (current) {
        // A student's program is sometimes listed again, e.g. on a later page.
        const existing = programs.find((p) => p.school.value === current!.school.value);
        if (existing) current = existing;
        else programs.push(current);
      }
    }

    const major = valueAfter(line, "major");
    if (major !== null && current) {
      const known = current.majors.some((m) => m.name === major);
      if (major && !major.includes("undeclared") && !known) {
        current.majors.push({ name: major, concentration: "" });
      }
    }

    const concentration = valueAfter(line, "concentration");
    if (concentration !== null && current?.majors.length) {
      const latest = current.majors[current.majors.length - 1];
      if (!latest.concentration) latest.concentration = concentration;
    }
  }

  return programs;
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
  // A transcript naming no concentration and one naming "Non Designated" mean the same thing,
  // so both look for the option that names none rather than for a close spelling.
  const preferred = NO_CONCENTRATION.has(wanted)
    ? closest.find((candidate) => NO_CONCENTRATION.has(candidate.concentration))
    : closest.find(
        (candidate) =>
          candidate.concentration &&
          distance(wanted, candidate.concentration) <= matchTolerance(candidate.concentration)
      );

  return (preferred ?? closest[0]).option;
};

// Given the programs read off a transcript, work out the student's selections. Under each school
// the first major listed is the one they are enrolled in, and any others are added on top of it.
export const detectSelections = (
  programs: ParsedProgram[],
  degrees: DegreeListing[] | undefined,
  majors: Major[] | undefined,
  startingYear: number | null
): SchoolSelection[] =>
  programs.map(({ school, majors: listed }) => {
    const [first, ...rest] = listed;

    const primary = first
      ? matchOption(
          first.name,
          first.concentration,
          getMajorOptions(degrees, school, startingYear),
          (option) => [option.value.major_name, option.value.concentration_name]
        ) ?? null
      : null;

    const additionalOptions = getAdditionalMajorOptions(majors, school, startingYear);
    const additional: MajorOptionItem[] = [];
    rest.forEach(({ name, concentration }) => {
      const match = matchOption(name, concentration, additionalOptions, (option) => [
        option.value.name ?? "",
        option.value.concentration_name ?? "",
      ]);
      if (match && !additional.includes(match)) additional.push(match);
    });

    return { school, primary, additional };
  });

// One academic record within a transcript. A submatriculant's transcript holds two — an
// undergraduate record and a "professional" one for the masters — each with its own program,
// majors, concentrations and institution credit.
type TranscriptRecord = {
  lines: string[];
};

// Marks the "Primary Program" line that opens each academic record.
const isProgramLine = (line: string) => line.replaceAll(" ", "").includes("program:");

// Splits a transcript into its academic records, each beginning at its `Program:` line. That
// line is followed, in the same column, by the degree, majors and concentrations belonging to
// the record, and then by the record's own transfer and institution credit.
//
// The `Level:` header cannot delimit records even though it names them: it sits in the page's
// right-hand column while the program block sits in the left, and a page is flattened left
// column first, so a record's level header can trail its own program block by dozens of lines.
// A high school record is instead dropped upstream, by `parseItems`.
//
// A transcript with no `Program:` line at all yields a single record holding every line, which
// is how transcripts parsed before records existed.
export const splitRecords = (textResult: string[]): TranscriptRecord[] => {
  const records: TranscriptRecord[] = [];

  textResult.forEach((line) => {
    if (isProgramLine(line) || !records.length) {
      records.push({ lines: [] });
    }
    records[records.length - 1].lines.push(line);
  });

  // Lines before the first program line belong to no record; drop that leading group unless it
  // is the only one, in which case it is the whole transcript.
  return records.length > 1 && !isProgramLine(records[0].lines[0])
    ? records.slice(1)
    : records;
};

// Reads one record's courses. Scanning a record at a time stops one record's
// `institution credit` from running on into the next record's courses.
const parseRecordCourses = (lines: string[]) => {
  const courseToSem: { [key: string]: string } = {};

  for (let l = 0; l < lines.length; l++) {
    if (lines[l].includes("transfer credit")) {
      Object.assign(courseToSem, getAPAndTransferCourses(lines, l));
    }

    if (lines[l].includes("institution credit")) {
      Object.assign(courseToSem, getCourseToSem(lines.slice(l + 1)));
    }
  }

  return courseToSem;
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

  // A submatriculant's shared courses appear on both records. Later records win, so a course
  // keeps the semester its most complete record gives it.
  splitRecords(textResult).forEach((record) => {
    Object.assign(courseToSem, parseRecordCourses(record.lines));
  });

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

  return {
    scrapedCourses: formattedSeparatedCourses,
    startYear: startYear,
    detectedSelections: detectSelections(
      parsePrograms(textResult),
      degrees,
      majors,
      startYear
    ),
  };
};
