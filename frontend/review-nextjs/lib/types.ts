import { FuseResult } from "fuse.js";

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

export type AutocompleteObject = {
    title: string;
    desc: string | Array<string>;
    url: string;
};

export type AutocompleteData = {
    courses: AutocompleteObject[];
    departments: AutocompleteObject[];
    instructors: AutocompleteObject[];
};

export type AutocompleteResult = {
    courses: FuseResult<AutocompleteObject>[];
    departments: FuseResult<AutocompleteObject>[];
    instructors: FuseResult<AutocompleteObject>[];
};
