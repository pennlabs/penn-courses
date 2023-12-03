import courses from "./courses";
import { IDegreePlan, IReq, IRule } from "@/models/Types";

const [course1, course2, course3, course4] = courses;

const degree_plan1: IDegreePlan = {
    program: "Engineering BSE",
    degree: "BSE",
    major: "CIS",
    year: 2023,
    concentration: "Artificial Intelligence"
}

const degree_plan2: IDegreePlan = {
    program: "Engineering BSE",
    degree: "BSE",
    major: "MEAM",
    year: 2023,
    concentration: "None"
}

const rule1: IRule = {
    courses: [course1, course2, course3],
    min_num: 3,
    max_num: 4,
    min_cus: 3,
    max_cus: 4,
    requirement: "EUT"
}

const req1: IReq = {
    name: "Technical Electives",
    code: "EUT",
    min_cus: 4,
    degree_plan: [degree_plan1], // where
    rules: [course1, course2, course3] // what 
}

const req2: IReq = {
    name: "CIS Core",
    code: "EUT",
    min_cus: 4,
    degree_plan: [degree_plan1],
    rules: []
}

export default [req1, req2];