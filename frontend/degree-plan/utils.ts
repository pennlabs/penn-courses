import { Course, DegreePlan, ParsedQObj, Rule } from "./types";

// Returns a callback that returns the rules a courses is expected to fulfill. This list of expected double counts should be a superset of the actual double counts
// (and a superset that is as tight as possible to the actual double counts)
export const expectedDoubleCounts = (activeDegreeplanDetail: DegreePlan) => {  // a flat list of rules
    if (!activeDegreeplanDetail) return [];
    const flatten: (rules: Rule[]) => Rule[] = (rules: Rule[]) => rules.flatMap(rule => [rule, ...flatten(rule.rules)] as Rule[]);
    const rulesList = activeDegreeplanDetail.degrees.flatMap(degree => flatten(degree.rules));

    // evaluate whether the course is expected to fulfill
    const courseSatisfiesQ = (course: Course, q_json: ParsedQObj): boolean => {
        switch (q_json.type) {
        case "COURSE":
            return q_json.full_code == course.id;
        case "SEARCH":
            return courseSatisfiesQ(course, q_json.q);
        case "LEAF":
            if (q_json.key === "full_code") return course.id == (q_json.value as string);
            if (q_json.key === "attributes__code__in") return course.attributes?.includes(q_json.value as string);
            if (q_json.key === "department__code" || q_json.key == "full_code__startswith") return course.id.startsWith(q_json.value as string);

            const code = course.id.split("-")[1]!; // expect this to always be defined 
            if (q_json.key === "code__gte") return code >= (q_json.value as string);
            if (q_json.key === "code__lte") return code <= (q_json.value as string);
            if (q_json.key === "code") return code == (q_json.value as string);

            const departmentCode = course.id.split("-")[0]!;
            if (q_json.key == "department__code__in") return (q_json.value as string[]).includes(departmentCode); 
            if (q_json.key == "semester") return true;
            return false; // this should never happen
        case "AND":
            return q_json.clauses.every(clause => courseSatisfiesQ(course, clause));
        case "OR":
            return q_json.clauses.some(clause => courseSatisfiesQ(course, clause));
        }
    }
    return (course: Course) => rulesList.filter(rule => courseSatisfiesQ(course, rule.q_json)).map(rule => rule.id);
}