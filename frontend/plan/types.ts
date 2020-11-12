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

export enum Day {
    M = "M",
    T = "T",
    W = "W",
    R = "R",
    F = "F",
    S = "S",
    U = "U",
}

export enum Color {
    RED = "#D0021B",
    ORANGE = "#F5A623",
    BLUE = "#00BFDD",
    AQUA = "#35E1BB",
    GREEN = "#7ED321",
    PINK = "#FF34CC",
    SEA = "#3055CC",
    INDIGO = "#7874CF",
    BLACK = "#000",
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

// Represents a single colored block on the schedule
export interface MeetingBlock {
    day: Day;
    start: number;
    end: number;
    course: {
        color: Color;
        id: string;
        coreqFulfilled: boolean;
    };
    style: {
        width: string;
        left: string;
    };
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
    crosslistings?: string[];
    requirements?: Requirement[];
    num_sections: number;
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

export enum SortMode {
    NAME = "Name",
    QUALITY = "Quality",
    DIFFICULTY = "Difficulty",
    GOOD_AND_EASY = "Good & Easy",
}
