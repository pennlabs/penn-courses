export enum Rating {
    Bad = "bad",
    Okay = "okay",
    Good = "good",
}

export type Course = {
    code: string;
    title: string;
    description: string;
    semester: string;
    quality: number | null;
    work: number | null;
    difficulty: number | null;
    current: boolean;
    instructors: string[];
    cleanCode: string;
};

export type Department = {
    code: string;
    name: string;
};

export type Instructor = {
    name: string;
    desc: string;
    id: string;
};

export type SearchOptions = {
    workLow: number;
    workHigh: number;
    difficultyLow: number;
    difficultyHigh: number;
    qualityLow: number;
    qualityHigh: number;
};

export type SearchResult = {
    Courses: Course[];
    Departments: Department[];
    Instructors: Instructor[];
};
