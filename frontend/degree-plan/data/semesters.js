import courses, {coursesFall2023, coursesSpring2023, coursesSpring2024} from "./courses"

export const semester1 = {
    name: "Fall 2022",
    courses: courses,
    cu: 5.5
}

export const semester2 = {
    name: "Spring 2023",
    courses: coursesSpring2023,
    cu: 5.5
}

export const semester3 = {
    name: "Fall 2023",
    courses: coursesFall2023,
    cu: 5.5
}

export const semester4 = {
    name: "Spring 2024",
    courses: coursesSpring2024,
    cu: 5.5
}

const semesters = [semester1, semester2, semester3, semester4];

export default semesters;