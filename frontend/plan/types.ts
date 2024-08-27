import { type User } from "pcx-shared-components/src/types";

export { type User } from "pcx-shared-components/src/types";

export enum School {
    SEAS = "SEAS",
    WHARTON = "WH",
    COLLEGE = "SAS",
    NURSING = "NURS",
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

export enum SortMode {
    NAME = "Name",
    QUALITY = "Quality",
    DIFFICULTY = "Difficulty",
    GOOD_AND_EASY = "Good & Easy",
    RECOMMENDED = "Suggested",
}

export interface Instructor {
    id: number;
    name: string;
}

export interface Section {
    id: string;
    status: Status;
    activity: Activity;
    credits: number;
    semester: string;
    meetings?: Meeting[];
    instructors: Instructor[];
    course_quality?: number;
    instructor_quality?: number;
    difficulty?: number;
    work_required?: number;
    associated_sections: Section[];
}

export interface Alert {
    id: string;
    section: string;
    cancelled: boolean;
    auto_resubscribe: boolean;
    close_notification: boolean;
    status: string;
}

export interface Meeting {
    id: string;
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
    // used for finding course conflicts
    id?: number;
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
    recommendation_score: number;
    work_required: number;
    crosslistings?: string[];
    requirements?: Requirement[];
    num_sections: number;
}

export interface CartCourse {
    section: Section;
    checked: boolean;
    overlaps: boolean;
}

export interface Schedule {
    id: string;
    sections: Section[];
    semester: string;
    name: string;
    created_at: string;
    updated_at: string;
}

export interface Friendship {
    sender: User;
    recipient: User;
    sent_at: string;
    accepted_at: string;
    status: string;
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
    days: {
        M: boolean;
        T: boolean;
        W: boolean;
        R: boolean;
        F: boolean;
        S: boolean;
        U: boolean;
    };
    time: [number, number];
    "schedule-fit": number;
    is_open: number;
}

export type FilterType =
    | number[]
    | [number, number]
    | { "1": boolean; "0.5": boolean; "1.5": boolean }
    | { [key: string]: boolean }
    | ActivityFilter
    | { LAB: boolean; REC: boolean; SEM: boolean; STU: boolean }
    | {
          M: boolean;
          T: boolean;
          W: boolean;
          R: boolean;
          F: boolean;
          S: boolean;
          U: boolean;
          time: [number, number];
      }
    | number;

    export interface FriendshipState {
        activeFriend: User;
        activeFriendSchedule: { found: boolean; sections: Section[] };
        acceptedFriends: User[];
        requestsReceived: Friendship[];
        requestsSent: Friendship[];
    }

    export interface ColorsMap {
        [key: string]: Color
    }