export enum School {
    SEAS = "SEAS",
    WHARTON = "WH",
    COLLEGE = "SAS",
    NURSING = "NUR",
}

export enum Status {
    OPEN = "O",
    CLOSED = "C",
    CANCELLED = "X",
    UNLISTED = "",
}

export enum Activity {
    CLINIC = "CLN",
    DISSERTATION = "DIS",
    INDEPENDENT_STUDY = "IND",
    LAB = "LAB",
    MASTERS_THESIS = "MST",
    RECITATION = "REC",
    SEMINAR = "SEM",
    SENIOR_THESIS = "SRT",
    STUDIO = "STU",
    UNDEFINED = "***",
}

export interface ActivityFilter {
    lab: boolean;
    rec: boolean;
    sem: boolean;
    stu: boolean;
}

export interface CUFilter {
    0.5: boolean;
    1.0: boolean;
    1.5: boolean;
}

export interface Section {
    id: string;
    status: Status;
    activity: Activity;
    credits: number;
    semester: string;
    meetings: Meeting[];
    instructors: string[];
    course_quality: number;
    instructor_quality: number;
    difficulty: number;
    work_required: number;
    associated_sections: Section[];
}

export interface Meeting {
    day: string;
    start: number;
    end: number;
    room: string;
}

export interface Profile {
    email: string | null;
    phone: string | null;
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

export interface Schedule {
    id: string;
    sections: Section[];
    semester: string;
    name: string;
    created_at: string;
    updated_at: string;
}

export interface User {
    username: string;
    first_name: string;
    last_name: string;
    profile: Profile;
}

export interface FilterData {
    searchString: string;
    searchType: string;
    selectedReq: { [K in string]: boolean };
    difficulty: [number, number];
    course_quality: [number, number]; // upper and lower bound for course_quality
    instructor_quality: [number, number];
    activity: ActivityFilter;
    cu: CUFilter;
}

export interface SearchObject {
    searchType: string;
}
