import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { schoolOptions } from "@/components/OnboardingPanels/SharedComponents";
import { DegreeListing, Major, Minor, SchoolOption } from "@/types";
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

// A program's catalog year marks when its requirements last changed, not a year it was offered,
// so a student who started in a given year is on the latest version from at or before it. The
// catalog doesn't reach back for every program, so one whose versions all came later takes its
// earliest, the closest to what the student started under.
const isBetterVersion = (year: number, than: number, startingYear: number) =>
  year <= startingYear
    ? than > startingYear || year > than
    : than > startingYear && year < than;

// Returns the version of each program that applies to a student who started in the given year.
const applicableVersions = <T extends { year: number }>(
  items: T[] | undefined,
  programOf: (item: T) => string,
  startingYear: number | null
): T[] | undefined => {
  if (!items) return undefined;
  if (!startingYear) return [];
  const versions = new Map<string, T>();
  items.forEach((item) => {
    const current = versions.get(programOf(item));
    if (!current || isBetterVersion(item.year, current.year, startingYear)) {
      versions.set(programOf(item), item);
    }
  });
  return [...versions.values()];
};

// What stays the same across the catalog years of a degree.
const degreeProgramOf = (degree: DegreeListing) =>
  [degree.program, degree.degree, degree.major, degree.concentration].join("|");

// Given a list of degrees and a school, return the primary majors the school offers, in every
// catalog year.
export const getMajorOptions = (
  degrees: DegreeListing[] | undefined,
  school: SchoolOption | null | undefined
): DegreeOption[] | undefined => {
  if (!degrees) return undefined;
  if (!school) return [];
  return degrees
    .filter((d) => d.degree === school.value)
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
export const degreeCodeOf = (programCode: string) => programCode.split("-")[1];

// A masters is a single program, so it takes no majors on top and can't be added to another degree.
const isMasters = (degreeCode: string) => degreeCode === "MSE";

// Whether a student can add majors on top of the one a school's degree includes.
export const takesAdditionalMajors = (school: SchoolOption) => !isMasters(school.value);

// Given the majors that can be added on top of a degree and a school, return the additional majors
// open to a student of that school, in every catalog year. A student can add a major from any
// school, so the school's own come first, and the rest name their degree: CSCI as a College major
// is not CSCI as an Engineering major.
export const getAdditionalMajorOptions = (
  majors: Major[] | undefined,
  school: SchoolOption | null | undefined
): MajorOptionItem[] | undefined => {
  if (!majors) return undefined;
  if (!school || !takesAdditionalMajors(school)) return [];
  const isOwn = (major: Major) => degreeCodeOf(major.program_code) === school.value;
  return majors
    .filter((major) => !isMasters(degreeCodeOf(major.program_code)))
    .map((major) => majorOption(major, school))
    .sort(
      (a, b) =>
        Number(isOwn(b.value)) - Number(isOwn(a.value)) || a.label.localeCompare(b.label)
    );
};

// An additional major as a school's card lists it: majors from other schools name their degree.
export const majorOption = (major: Major, school: SchoolOption): MajorOptionItem => {
  const name = major.concentration_name
    ? `${major.name} - ${major.concentration_name}`
    : major.name;
  const own = degreeCodeOf(major.program_code) === school.value;
  const degree = own ? "" : `, ${degreeCodeOf(major.program_code)}`;
  return { value: major, label: `${name} (${major.year}${degree})` };
};

export type MinorOptionItem = {
  value: Minor;
  label: string;
};

export const minorOption = (minor: Minor): MinorOptionItem => ({
  value: minor,
  label: `${minor.name ?? minor.code} (${minor.year})`,
});

export const getMinorOptions = (minors: Minor[] | undefined): MinorOptionItem[] | undefined =>
  minors?.map(minorOption).sort((a, b) => a.label.localeCompare(b.label));

// A school, the major the student is enrolled in through it, and the majors they add on top.
export type SchoolSelection = {
  // Tells apart two cards for the same school, which a plan can hold; defaults to the school.
  key?: string;
  school: SchoolOption;
  primary: DegreeOption | null;
  additional: MajorOptionItem[];
  minors?: MinorOptionItem[];
};

// What a transcript says about one program: a school and the majors and minors listed under it,
// in order.
type ParsedProgram = {
  school: SchoolOption;
  majors: { name: string; concentration: string }[];
  minors: string[];
  // The year the program's record began, or null if its record names no semester.
  startYear: number | null;
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
// on into the course listing or the transcript totals next to it, which are cut off.
const RUN_ON = /\s+subj\s+no\.|\s*_{5,}|\s+[a-z]{2,5}\s\d{4}\b|\s+total\s+institution\b|\s+\d+\.\d{2}\b/;

const valueAfter = (line: string, label: string): string | null => {
  const match = line.match(new RegExp(`\\b${label}\\s*:\\s*(.*)$`));
  if (!match) return null;
  return match[1].split(RUN_ON)[0].trim();
};

// A transcript names several minors under one "Minor :" label, one per line. A line that carries
// its own label, or starts the course listing, ends the list.
const continuedMinor = (line: string): string | null => {
  // The leading space lets RUN_ON also match at the start, where the listing or totals begin.
  const value = ` ${line}`.split(RUN_ON)[0].trim();
  if (!value || /:/.test(value) || /\d/.test(value)) return null;
  return value;
};

// Given a transcript's records, return each program it lists with the majors and minors under it.
// A major or minor belongs to the closest program above it, and a concentration to the major
// above it. Each
// program takes the start year of the record it is listed in.
export const parsePrograms = (
  records: { lines: string[]; startYear: number | null }[]
): ParsedProgram[] => {
  const programs: ParsedProgram[] = [];
  let current: ParsedProgram | undefined;

  records.forEach(({ lines, startYear }) => {
    let readingMinors = false;
    for (let l = 0; l < lines.length; l++) {
      const line = lines[l];

      if (readingMinors && current) {
        const more = continuedMinor(line);
        if (more && !current.minors.includes(more)) current.minors.push(more);
        if (!more) readingMinors = false;
      }

      if (PROGRAM_LINE.test(line)) {
        const school = detectSchool(programHeader(lines, l));
        // A program that isn't one of our schools takes its majors with it.
        current = school && { school, majors: [], minors: [], startYear };
        if (current) {
          // A student's program is sometimes listed again, e.g. on a later page. It keeps the
          // year of its first listing, since a later page's record starts partway through.
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

      const minor = valueAfter(line, "minor");
      if (minor && current && !current.minors.includes(minor)) current.minors.push(minor);
      if (minor !== null) readingMinors = true;

      const concentration = valueAfter(line, "concentration");
      if (concentration !== null && current?.majors.length) {
        const latest = current.majors[current.majors.length - 1];
        if (!latest.concentration) latest.concentration = concentration;
      }
    }
  });

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

const AMBIGUOUS = Symbol("ambiguous");

// Returns the option whose program name is closest to the transcript's wording, or undefined
// if no option is close enough. Ties are broken by matching concentration, then by exact wording.
// AMBIGUOUS means the name matched but the concentration couldn't settle which version.
const matchOptionOrAmbiguous = <T>(
  major: string,
  concentration: string,
  options: T[] | undefined,
  namesOf: (option: T) => [string, string]
): T | typeof AMBIGUOUS | undefined => {
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
  const concentrationMatches = (candidate: typeof scored[number]) =>
    NO_CONCENTRATION.has(wanted)
      ? NO_CONCENTRATION.has(candidate.concentration)
      : Boolean(candidate.concentration) &&
        distance(wanted, candidate.concentration) <=
          matchTolerance(candidate.concentration);

  const withConcentration = closest.filter(concentrationMatches);
  // With no concentration named and every version having one, any pick would be a guess.
  if (
    !withConcentration.length &&
    NO_CONCENTRATION.has(wanted) &&
    new Set(closest.map((candidate) => candidate.concentration)).size > 1
  ) {
    return AMBIGUOUS;
  }
  const pool = withConcentration.length ? withConcentration : closest;
  pool.sort(
    (a, b) => Number(b.concentration === wanted) - Number(a.concentration === wanted)
  );

  return pool[0].option;
};

const matchOption = <T>(
  major: string,
  concentration: string,
  options: T[] | undefined,
  namesOf: (option: T) => [string, string]
): T | undefined => {
  const match = matchOptionOrAmbiguous(major, concentration, options, namesOf);
  return match === AMBIGUOUS ? undefined : match;
};

// Given the programs read off a transcript, work out the student's selections. Under each school
// the first major listed is the one they are enrolled in, and any others are added on top of it.
// Each program is matched against the versions in force the year its own record began, falling
// back to the plan's starting year.
export const detectSelections = (
  programs: ParsedProgram[],
  degrees: DegreeListing[] | undefined,
  majors: Major[] | undefined,
  minors: Minor[] | undefined,
  startingYear: number | null
): SchoolSelection[] => {
  // A plan holds each minor once, under one degree, so a minor listed twice goes to the first.
  const placedMinorIds = new Set<number>();
  return programs.map(({ school, majors: listed, minors: listedMinors, startYear: programStart }) => {
    const year = programStart ?? startingYear;
    const [first, ...rest] = listed;

    const primary = first
      ? matchOption(
          first.name,
          first.concentration,
          getMajorOptions(applicableVersions(degrees, degreeProgramOf, year), school),
          (option) => [option.value.major_name, option.value.concentration_name]
        ) ?? null
      : null;

    const additionalOptions = getAdditionalMajorOptions(
      applicableVersions(majors, (major) => major.program_code, year),
      school
    );
    const additional: MajorOptionItem[] = [];
    const namesOf = (option: MajorOptionItem): [string, string] => [
      option.value.name ?? "",
      option.value.concentration_name ?? "",
    ];
    const isOwn = (option: MajorOptionItem) =>
      degreeCodeOf(option.value.program_code) === school.value;
    rest.forEach(({ name, concentration }) => {
      // A major the school offers itself wins over one from elsewhere, however close that is.
      const own = matchOptionOrAmbiguous(
        name,
        concentration,
        additionalOptions?.filter(isOwn),
        namesOf
      );
      if (own === AMBIGUOUS) return;
      const match = own ?? matchOption(name, concentration, additionalOptions, namesOf);
      if (match && !additional.includes(match)) additional.push(match);
    });

    // The minors list names each "Minor in X", where a transcript says just "X".
    const minorOptions = takesAdditionalMajors(school)
      ? getMinorOptions(applicableVersions(minors, (minor) => minor.program_code, year))
      : [];
    const chosenMinors: MinorOptionItem[] = [];
    listedMinors.forEach((name) => {
      const match = matchOption(name, "", minorOptions, (option) => [
        (option.value.name ?? "").replace(/^minor in /i, ""),
        "",
      ]);
      if (match && !placedMinorIds.has(match.value.id)) {
        placedMinorIds.add(match.value.id);
        chosenMinors.push(match);
      }
    });

    return { school, primary, additional, minors: chosenMinors };
  });
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

// Which of a submatriculant's degrees a course is on the books for, as the backend names them.
// A course on both records is the double counted kind; one on a single record counts only there.
export type CourseLevel = "UNDERGRADUATE" | "GRADUATE" | "SHARED";

// True for the record of a masters degree.
const isMastersRecord = (lines: string[]) =>
  lines.some(
    (line, l) =>
      isProgramLine(line) && detectSchool(programHeader(lines, l))?.value === "MSE"
  );

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
// Coordinated programs, by how a transcript's program lines name them. M&T reads e.g.
// "Program: School of Engineering and Applied Science - Fisher Program in Management & Technology".
const DUAL_PROGRAM_NAMES: [string, RegExp][] = [
  ["HUNTSMAN", /huntsman/i],
  ["MT", /jerome fisher|management (&|and) technology/i],
  ["LSM", /life sciences (&|and) management/i],
  ["VIPER", /vagelos integrated|energy research/i],
];

// The code of the coordinated program a transcript names, or null. Only lines naming a program
// are read, so a course title such as "M&T First Year Seminar" can't trigger it.
export const detectDualProgram = (lines: string[]): string | null => {
  const programLines = lines.filter((line) => /program/i.test(line)).join(" ");
  return DUAL_PROGRAM_NAMES.find(([, name]) => name.test(programLines))?.[0] ?? null;
};

export const parseTranscript = (
  textResult: string[],
  degrees: DegreeListing[] | undefined,
  majors: Major[] | undefined,
  minors: Minor[] | undefined
) => {
  let courseToSem: { [key: string]: string } = {};
  let startYear: number = 0;

  // Earliest year named by the semesters, or null (e.g. only _TRAN).
  const firstYear = (sems: string[]): number | null => {
    const years = sems
      .map((sem) => parseInt(sem.replace(/\D/g, ""), 10))
      .filter((y) => !isNaN(y));
    return years.length ? Math.min(...years) : null;
  };

  const records = splitRecords(textResult).map(({ lines }) => {
    const recordCourses = parseRecordCourses(lines);
    return {
      lines,
      recordCourses,
      graduate: isMastersRecord(lines),
      startYear: firstYear(Object.values(recordCourses)),
    };
  });

  // A submatriculant's masters record comes first on the transcript; take records in the order
  // they were begun. Their shared courses appear on both records, and later records win, so a
  // course keeps the semester its most complete record gives it.
  [...records]
    .sort((a, b) => (a.startYear ?? Infinity) - (b.startYear ?? Infinity))
    .forEach(({ recordCourses }) => Object.assign(courseToSem, recordCourses));

  // A course on the masters record only counts toward the masters, one on the undergraduate
  // record only toward the bachelors, and one on both is double counted. A transcript with no
  // masters record says nothing about this, so its courses are left unmarked.
  const courseLevels: { [course: string]: CourseLevel } = {};
  if (records.some((record) => record.graduate)) {
    records.forEach((record) => {
      const level: CourseLevel = record.graduate ? "GRADUATE" : "UNDERGRADUATE";
      Object.keys(record.recordCourses).forEach((course) => {
        const seen = courseLevels[course];
        courseLevels[course] = seen && seen !== level ? "SHARED" : level;
      });
    });
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
    // Chronological order: the panel displays this, and the backend gives the submatriculation
    // double counting allowance to the earliest courses it receives.
  ).sort((a, b) => semesterIndex(a.sem) - semesterIndex(b.sem));

  startYear = firstYear(formattedSeparatedCourses.map(({ sem }) => sem)) ?? 0;

  return {
    scrapedCourses: formattedSeparatedCourses,
    courseLevels,
    startYear: startYear,
    detectedSelections: detectSelections(
      parsePrograms(records),
      degrees,
      majors,
      minors,
      startYear
    ),
    detectedDualProgram: detectDualProgram(textResult),
  };
};
