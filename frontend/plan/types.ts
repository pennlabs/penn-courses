export interface Section {
    id: string;
}
export enum School {
    SEAS = "SEAS",
    WHARTON = "WH",
    COLLEGE = "SAS",
    NURSING = "NUR",
}
export interface Requirement {
    id: string;
    code: string;
    school: School;
    semester: string;
    name: string;
}

export interface Course {
    id: string;
    title: string;
    sections: Section[];
    description: string;
    semester: string;
    prerequisites: string;
    course_quality: number;
    instructor_quality: number;
    difficulty: number;
    work_required: number;
    crosslistings: string[];
    requirements: Requirement[];
}
