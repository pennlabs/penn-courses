import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import { DegreeListing, SchoolOption } from "@/types";
const { closest } = require("fastest-levenshtein");

export const parseItems = (items: any[], index: number) => {
  // At most the transcript will have two columns - we account for that here.
  let allText: any = { col0: [], col1: [] };

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

    let currentCol = col < maxCol ? "col0" : "col1";

    // Ignore potential high school program transcript
    if (items[i].str === "Level:High School") {
      allText[currentCol] = [];
      break;
    }
    if (pos in allText[currentCol])
      allText[currentCol][pos].push(items[i]?.str);
    else allText[currentCol][pos] = [items[i]?.str];
  }

  return allText;
};

export const getMajorOptions = (
  degrees: DegreeListing[] | undefined,
  schools: SchoolOption[],
  startingYear: any
) => {
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

export const parseTranscript = (
  textResult: any,
  degrees: DegreeListing[] | undefined
) => {
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
        if (
          textResult[parseInt(l) + 1].includes(
            "bachelor of science in engineering"
          )
        )
          tempSchools.push({ value: "BSE", label: "Engineering BSE" });
        else tempSchools.push({ value: "BAS", label: "Engineering BAS" });
      }
      if (program.includes("wharton"))
        tempSchools.push({ value: "BS", label: "Wharton" });
      if (program.includes("nursing"))
        tempSchools.push({ value: "BSN", label: "Nursing" });
    }

    // SCRAPE MAJOR
    if (textResult[l].includes("major")) {
      detectedMajors.push(textResult[l].replace(/^.*?:\s*/, ""));
    }

    // SCRAPE CONCENTRATION
    if (textResult[l].includes("concentration")) {
      detectedConcentrations.push(textResult[l].replace(/^.*?:\s*/, ""));
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
    let firstNonSummerSemReached = false;
    
    let courseToSem: { [key: string]: string } = {};
    
    if (textResult[l].includes("institution credit")) {
      let truncatedTranscript = textResult.slice(parseInt(l) + 1);
      let currentSem = "";
      for (let line of truncatedTranscript) {
        if (/(fall|spring|summer)\s\d{4}/i.test(line)) {
          currentSem = line;
          if (!firstNonSummerSemReached && !currentSem.includes("summer")) {
            firstNonSummerSemReached = true;
          }
          // Only start creating sems after first non-summer semester is reached
          if (firstNonSummerSemReached) {
            separatedCourses[currentSem] = [];
          }
        } else {
          let courseMatch = line.match(/\b\w+\s\d{3,4}\b/);
          
          if (courseMatch) {
            // Check if course didn't get an F or a W. If so, add to current sem or _TRAN           
            if (!(line[line.length - 1] == "f" || line[line.length - 1] == "w")) {
              // TODO: We don't yet have a way to track courses that can be taken multiple times, 
              // so we store a course that appears multiple times only in the most recent semester it appears in.
              if (courseMatch[0] in courseToSem) {
                const prevSem = courseToSem[courseMatch[0]];
                separatedCourses[currentSem].push(courseMatch[0]);
                courseToSem[courseMatch[0]] = currentSem;
                separatedCourses[prevSem] = separatedCourses[prevSem].filter((c: string) => c !== courseMatch[0]);
              } else {
                // Add all pre-college courses to _TRAN semester
                if (firstNonSummerSemReached) {
                  separatedCourses[currentSem].push(courseMatch[0]);
                  courseToSem[courseMatch[0]] = currentSem;
                } else {
                  separatedCourses["_TRAN"].push(courseMatch[0]);
                  courseToSem[courseMatch[0]] = "_TRAN";
                }
              }
            }
          }
        }
      }

      // Remove any empty semesters (handles edge case where user fails/withdraws from all courses in a semester)
      for (let sem of Object.keys(separatedCourses)) {
        if (separatedCourses[sem].length == 0) {
          delete separatedCourses[sem];
        }
      }
      
      separatedCourses = Object.keys(separatedCourses).map(
        (key) => ({ sem: key, courses: separatedCourses[key] })
      );

      // SCRAPE START YEAR AND INFER GRAD YEAR
      let years = separatedCourses.map((e: any, i: number) => {
        return parseInt(e.sem.replace(/\D/g, ""));
      });
      years.shift();
      startYear = Math.min(...years);
    }
  }

  // Match majors
  let detectedMajorsOptions = [];

  let possibleDegrees = getMajorOptions(degrees, tempSchools, startYear);
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
  return {
    scrapedCourses: separatedCourses,
    startYear: startYear,
    scrapedSchools: tempSchools,
    detectedMajorsOptions: detectedMajorsOptions,
  };
};
