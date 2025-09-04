import { FuseResult } from "fuse.js";

export enum Rating {
    Bad = "bad",
    Okay = "okay",
    Good = "good",
}

export type Course = {
    code: string;
    last_offered_sem_if_superceded: string | null;
    description: string;
    aliases: string[];
    historical_codes: {
        full_code: string;
        semester: string;
        branched_from: boolean;
    }[];
    latest_semester: string;
    num_sections: number;
    num_sections_recent: number;
    instructors: Instructor[];
    registration_metrics: boolean;
    average_reviews: {
        rInstructorQuality: number;
        rCourseQuality: number;
        rCommunicationAbility: number;
        rStimulateInterest: number;
        rInstructorAccess: number;
        rDifficulty: number;
        rWorkRequired: number;
        rTaQuality: number;
        rReadingsValue: number;
        rAmountLearned: number;
        rRecommendMajor: number;
        rRecommendNonmajor: number;
        rFinalEnrollment: number;
        rPercentOpen: number;
        rNumOpenings: number;
        rFilledInAdvReg: number;
        rSemesterCalc: string;
        rSemesterCount: number;
    };
    recent_reviews: {
        rInstructorQuality: number;
        rCourseQuality: number;
        rCommunicationAbility: number;
        rStimulateInterest: number;
        rInstructorAccess: number;
        rDifficulty: number;
        rWorkRequired: number;
        rTaQuality: number;
        rReadingsValue: number;
        rAmountLearned: number;
        rRecommendMajor: number;
        rRecommendNonmajor: number;
        rFinalEnrollment: number;
        rPercentOpen: number;
        rNumOpenings: number;
        rFilledInAdvReg: number;
        rSemesterCalc: string;
        rSemesterCount: number;
    };
    num_semesters: number;
};

export type Department = {
    code: string;
    name: string;
};

export type Instructor = {
    id: number;
    average_reviews: Object;
    recent_reviews: Object;
    latest_semester: string;
    name: string;
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
