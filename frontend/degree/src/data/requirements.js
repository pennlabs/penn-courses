import courses from "./courses";

const [course1, course2, course3, course4] = courses;

const req1 = {
    name: "CIS Core",
    courses: [course1, course2]
}
const req2 = {
    name: "CIS Electives",
    courses: [course3, course4]
}

export default [req1, req2];