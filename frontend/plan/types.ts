export interface Section {
    id: string;
    status: Status;
    activity: Activity;
    meetings: Meeting[];
    credits: number;
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
    credits: number;
    semester: string;
    meetings: Meeting[];
    instructors: string[];
    course_quality: number;
    instructor_quality: number;
    difficulty: number;
    work_required: number;
    associated_sections: Section[];
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
