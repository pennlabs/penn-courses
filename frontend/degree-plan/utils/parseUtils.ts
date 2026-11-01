import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { DegreeListing, Major, SchoolOption } from "@/types";
import { MT_UNDECLARED_PROGRAM, isMandTDegree, suitsMandT } from "@/utils/programs";
const { distance } = require("fastest-levenshtein");

// How far a transcript's wording may sit from a program's name and still be the same thing.
const matchTolerance = (name: string) => Math.max(3, Math.floor(name.length / 3));

const normalize = (text: string) => text.toLowerCase().replace(/\s+/g, " ").trim();

// Keeps the first item for each key. A submatriculant's records can name the same school or
// degree twice, and the onboarding selects should offer it once.
const dedupeBy = <T, K>(items: T[], keyOf: (item: T) => K): T[] => {
  const seen = new Set<K>();
  return items.filter((item) => {
    const key = keyOf(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

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

// Distance between a catalog year and the year the student started; 0 when the start is unknown.
const yearDistance = (year: number, startYear: number | null) =>
  startYear ? Math.abs(year - startYear) : 0;

// Sort key placing semesters in the order taken, transfer credit first.
const semesterIndex = (sem: string) => {
  const year = parseInt(sem.replace(/\D/g, ""), 10);
  if (isNaN(year)) return -Infinity;
  if (/spring/i.test(sem)) return year * 3;
  if (/summer/i.test(sem)) return year * 3 + 1;
  return year * 3 + 2;
};

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
    .sort(
      (a, b) =>
        yearDistance(a.year, startingYear) - yearDistance(b.year, startingYear)
    )
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

const WHARTON = { value: "BS", label: "Wharton" };
const SEAS_BSE = { value: "BSE", label: "Engineering BSE" };
const SEAS_BAS = { value: "BAS", label: "Engineering BAS" };

// The Jerome Fisher Program in Management & Technology, a dual degree in Wharton and SEAS. Its
// transcripts hold one record per school, each program named "... - Jerome Fisher Program in
// Management & Technology". The name wraps across lines, so this is tested on joined text.
const isMandTText = (text: string) =>
  /management\s*(&|and)\s*technology|jerome\s+fisher/.test(text);

// A program's name wraps onto the lines after its `Program:` line, e.g.
//   Program: School of Engineering and Applied Science -
//            Bachelor of Science in Engineering - Jerome
//            Fisher Program in Management & Technology
//   Division : School of Engineering and Applied Science
// Returns the whole name, which ends at the record's next labelled field.
const programText = (textResult: string[], l: number) => {
  const parts = [textResult[l].replace(/^.*?:\s*/, "")];
  for (let next = l + 1; next < textResult.length && next <= l + 4; next++) {
    const line = textResult[next];
    if (line.includes(":") || line.includes("program(s)")) break;
    parts.push(line);
  }
  return normalize(parts.join(" "));
};

// Given a string[] where we're guaranteed to have a school line, return a list of scraped schools.
const checkSchool = (textResult: string[], l: number) => {
  const tempSchools = [];
  const program = programText(textResult, l);
  if (program.includes("arts"))
    tempSchools.push({ value: "BA", label: "Arts & Sciences" });
  if (program.includes("engineering and applied science")) {
    // SEAS names the degree within the program's name. A submatriculant's masters record names
    // a MSE there, which would otherwise fall through to the BAS branch and read as a second
    // bachelors.
    if (program.includes("bachelor of science in engineering"))
      tempSchools.push(SEAS_BSE);
    else if (program.includes("master of science in engineering"))
      tempSchools.push({ value: "MSE", label: "Engineering MSE" });
    else tempSchools.push(SEAS_BAS);
  }
  if (program.includes("wharton")) tempSchools.push(WHARTON);
  if (program.includes("nursing"))
    tempSchools.push({ value: "BSN", label: "Nursing" });

  return tempSchools;
};

// The transcript's program names joined. Only these count, so a course title cannot mark a
// transcript as M&T.
const programNames = (textResult: string[]) =>
  textResult
    .map((line, l) => (isProgramLine(line) ? programText(textResult, l) : ""))
    .join(" ");

const isMandTTranscript = (textResult: string[]) => isMandTText(programNames(textResult));

// An M&T student is always in both Wharton and SEAS. If a transcript names the program but either
// school's record was worded in a way `checkSchool` missed, add that school back.
const withMandTSchools = (
  textResult: string[],
  schools: { value: string; label: string }[]
) => {
  const text = programNames(textResult);
  if (!isMandTText(text)) return schools;
  const has = (value: string) => schools.some((school) => school.value === value);
  const added = [...schools];
  if (!has(WHARTON.value)) added.push(WHARTON);
  if (!has(SEAS_BSE.value) && !has(SEAS_BAS.value)) {
    added.push(text.includes("bachelor of applied science") ? SEAS_BAS : SEAS_BSE);
  }
  return added;
};

// A course line carries its course units, e.g. `cis 1200 prog lang & tech i 1.00 a`. A long
// title's continuation on the next line carries none, even when it reads like a course or a
// year ("major authors since 1900").
const CREDITS = /\b\d+\.\d{2}\b/;

// Grades of a course that does not count. A line can end in a space, so the grade is its last
// word rather than its last character.
const FAILED_GRADES = new Set(["f", "w"]);
const gradeOf = (line: string) => line.trim().split(/\s+/).pop() ?? "";

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
      CREDITS.test(line) &&
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
      if (courseMatch && CREDITS.test(line)) {
        // Check if course didn't get an F or a W. If so, add to current sem or _TRAN
        if (!FAILED_GRADES.has(gradeOf(line))) {
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

// The words of a program name that carry meaning, with "&" read as "and".
const NAME_FILLER = new Set(["and", "of", "in", "the", "for"]);
const nameWords = (name: string) =>
  normalize(name)
    .replace(/&/g, " and ")
    .split(/[^a-z0-9]+/)
    .filter((word) => word && !NAME_FILLER.has(word));

// Whether `short` is an abbreviation of `long`: a word starting the same and keeping the rest of
// its letters in order, as "engr" does "engineering" and "mgmt" does "management".
const abbreviatesWord = (short: string, long: string) => {
  if (short === long) return true;
  if (short.length < 2 || short[0] !== long[0]) return false;
  let at = 0;
  for (const letter of long) if (letter === short[at]) at++;
  return at === short.length;
};

// Whether one program name abbreviates another word for word, as "Bus Econ & Public Policy" does
// "business economics and public policy". Both must have the same number of words, so a shorter
// name never matches a longer program that merely starts the same way.
export const abbreviates = (short: string, long: string) => {
  const shortWords = nameWords(short);
  const longWords = nameWords(long);
  return (
    shortWords.length > 0 &&
    shortWords.length === longWords.length &&
    shortWords.every((word, i) => abbreviatesWord(word, longWords[i]))
  );
};

// Returns the option whose program name is closest to the transcript's wording, or undefined
// if no option is close enough. Ties are broken by matching concentration, then by the catalog
// year nearest the student's start, then by exact wording.
const matchOption = <T>(
  major: string,
  concentration: string,
  startYear: number | null,
  options: T[] | undefined,
  namesOf: (option: T) => [string, string],
  yearOf: (option: T) => number
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
      yearDistance: yearDistance(yearOf(option), startYear),
    };
  });

  const best = Math.min(...scored.map((candidate) => candidate.distance));
  let closest = scored.filter((candidate) => candidate.distance === best);
  // Transcripts spell a program out ("mechanical engineering and applied mechanics") where the
  // catalog may hold Path's abbreviation of it ("Mech Engr & Appl Mechanics"), which no edit
  // distance tolerance bridges.
  if (best > matchTolerance(closest[0].name)) {
    closest = scored.filter((candidate) => abbreviates(candidate.name, target));
    if (!closest.length) return undefined;
  }

  const wanted = normalize(concentration);
  // A transcript naming no concentration and one naming "Non Designated" mean the same thing,
  // so both look for the option that names none rather than for a close spelling.
  const concentrationMatches = (candidate: typeof scored[number]) =>
    NO_CONCENTRATION.has(wanted)
      ? NO_CONCENTRATION.has(candidate.concentration)
      : Boolean(candidate.concentration) &&
        (distance(wanted, candidate.concentration) <=
          matchTolerance(candidate.concentration) ||
          abbreviates(candidate.concentration, wanted));

  const withConcentration = closest.filter(concentrationMatches);
  const pool = withConcentration.length ? withConcentration : closest;
  pool.sort(
    (a, b) =>
      a.yearDistance - b.yearDistance ||
      Number(b.concentration === wanted) - Number(a.concentration === wanted)
  );

  return pool[0].option;
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
  possibleMajors: MajorOptionItem[] | undefined,
  startYear: number | null = null
) => {
  const degreeOptions: DegreeOption[] = [];
  const majorOptions: MajorOptionItem[] = [];

  detectedMajors.forEach((major, i) => {
    if (!major || major.includes("undeclared")) return;
    const concentration = detectedConcentrations[i] ?? "";

    const degree = matchOption(
      major,
      concentration,
      startYear,
      possibleDegrees,
      (option) => [option.value.major_name, option.value.concentration_name],
      (option) => option.value.year
    );
    if (degree) {
      degreeOptions.push(degree);
      return;
    }

    const standalone = matchOption(
      major,
      concentration,
      startYear,
      possibleMajors,
      (option) => [
        option.value.name ?? "",
        option.value.concentration_name ?? "",
      ],
      (option) => option.value.year
    );
    if (standalone) majorOptions.push(standalone);
  });

  return { degreeOptions, majorOptions };
};

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

type ParsedRecord = {
  schools: { value: string; label: string }[];
  majors: string[];
  concentrations: string[];
  courseToSem: { [key: string]: string };
};

// A record's labelled major and concentration fields ("major : computer science", "second major :
// ..."), as opposed to a course title that happens to contain the word ("major authors").
const MAJOR_FIELD = /^\s*(?:[a-z]+\s+)?major\s*:/;
const CONCENTRATION_FIELD = /^\s*(?:[a-z]+\s+)?concentration\s*:/;

// Reads one record's program, majors, concentrations and courses. Scanning a record at a time
// keeps each record's majors paired with its own concentrations, and stops one record's
// `institution credit` from running on into the next record's courses.
const parseRecord = (lines: string[]): ParsedRecord => {
  const record: ParsedRecord = {
    schools: [],
    majors: [],
    concentrations: [],
    courseToSem: {},
  };

  for (let l = 0; l < lines.length; l++) {
    if (isProgramLine(lines[l])) {
      record.schools = record.schools.concat(checkSchool(lines, l));
    }

    if (MAJOR_FIELD.test(lines[l])) {
      record.majors.push(lines[l].replace(/^.*?:\s*/, ""));
    }

    if (CONCENTRATION_FIELD.test(lines[l])) {
      record.concentrations.push(lines[l].replace(/^.*?:\s*/, ""));
    }

    if (lines[l].includes("transfer credit")) {
      Object.assign(record.courseToSem, getAPAndTransferCourses(lines, l));
    }

    if (lines[l].includes("institution credit")) {
      Object.assign(record.courseToSem, getCourseToSem(lines.slice(l + 1)));
    }
  }

  return record;
};

// The degree whose catalog year is nearest the student's start.
const nearestYear = (
  degrees: DegreeListing[] | undefined,
  startYear: number | null
): DegreeListing | undefined =>
  degrees
    ?.slice()
    .sort((a, b) => yearDistance(a.year, startYear) - yearDistance(b.year, startYear))[0];

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

  // Earliest year named by the semesters, or null (e.g. only _TRAN).
  const firstYear = (sems: string[]): number | null => {
    const years = sems
      .map((sem) => parseInt(sem.replace(/\D/g, ""), 10))
      .filter((y) => !isNaN(y));
    return years.length ? Math.min(...years) : null;
  };

  // A submatriculant's masters record comes first on the transcript; take records in the order
  // they were begun.
  const parsedRecords = splitRecords(textResult)
    .map((record) => parseRecord(record.lines))
    .map((record) => ({
      ...record,
      startYear: firstYear(Object.values(record.courseToSem)),
    }))
    .sort((a, b) => (a.startYear ?? Infinity) - (b.startYear ?? Infinity));

  parsedRecords.forEach((record) => {
    tempSchools = tempSchools.concat(record.schools);
    // A submatriculant's shared courses appear on both records. Later records win, so a course
    // keeps the semester its most complete record gives it.
    Object.assign(courseToSem, record.courseToSem);
  });
  tempSchools = withMandTSchools(textResult, tempSchools);

  // Chronological order: the panel displays this, and the backend gives the submatriculation
  // double counting allowance to the earliest courses it receives.
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
  ).sort((a, b) => semesterIndex(a.sem) - semesterIndex(b.sem));

  startYear = firstYear(formattedSeparatedCourses.map(({ sem }) => sem)) ?? 0;

  const secondMajorPool = getSecondMajorOptions(majors, startYear);
  const degreeOptions: DegreeOption[] = [];
  const majorOptions: MajorOptionItem[] = [];

  // An M&T transcript matches the M&T versions of its Wharton and SEAS degrees, and any other
  // transcript only the ordinary ones, since the two carry the same names. A catalog that has no
  // M&T degrees yet (they come from a fetch_degrees_from_path run) falls back to the ordinary
  // ones rather than matching nothing.
  const mandT = isMandTTranscript(textResult) && !!degrees?.some(isMandTDegree);
  const programDegrees = degrees?.filter((degree) => suitsMandT(degree, mandT));

  parsedRecords.forEach((record) => {
    if (!record.majors.length) return;
    // A record whose school went unrecognised matches against every school on the transcript,
    // including any `withMandTSchools` added back.
    const recordSchools = record.schools.length ? record.schools : tempSchools;
    // A masters record begins years after the undergraduate one, so match on its own start.
    const recordStart = record.startYear ?? startYear;
    const detected = detectMajors(
      record.majors,
      record.concentrations,
      getMajorOptions(programDegrees, recordSchools, recordStart),
      secondMajorPool,
      recordStart
    );
    degreeOptions.push(...detected.degreeOptions);
    majorOptions.push(...detected.majorOptions);

    // An M&T student who has not chosen a Wharton concentration still has a Wharton degree.
    const undeclaredWharton =
      mandT &&
      recordSchools.some((school) => school.value === WHARTON.value) &&
      record.majors.some((major) => major.includes("undeclared"));
    if (undeclaredWharton) {
      const undeclared = nearestYear(
        programDegrees?.filter((degree) => degree.program === MT_UNDECLARED_PROGRAM),
        recordStart
      );
      if (undeclared) degreeOptions.push({ value: undeclared, label: createMajorLabel(undeclared) });
    }
  });

  return {
    scrapedCourses: formattedSeparatedCourses,
    startYear: startYear,
    scrapedSchools: dedupeBy(tempSchools, (school) => school.value),
    detectedMajorsOptions: dedupeBy(degreeOptions, (option) => option.value.id),
    detectedSecondMajorOptions: dedupeBy(
      majorOptions,
      (option) => option.value.id
    ),
  };
};
