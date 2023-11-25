export type IYear = {
    name: string,
    semesters: ISemester[]
}

export type ISemester = {
    name: string,
    courses: ICourse[]
}

export type ICourse = {
    id: string,
    title: string,
    description: string,
    semester: string,
    num_sections: number,
    course_quality: number,
    instructor_quality: number,
    difficulty: number,
    work_required: number,
    recommendation_score: number,
    added: boolean,
    dept: string,
    number: string,
}

export type ICourseQ = {
    dept: string,
    number: string,
    title: string,
    semester: string
}

// enum QualifierType {
//     GPA = "GPA",
//     CUS = "CUS",
//     NUM = "NUM"
// }

// export type IQualifier = {
//     label: string,
//     code: string,
//     min_cus: Number,
//     num: Number,
//     type: QualifierType
// }


export type IDegreePlan = {
    program: string,
    degree: string,
    major: string,
    concentration: string,
    year: Number
}

/* This model represents a degree requirement. */ 
export type IReq = {
    name: string,
    code: string,
    min_cus: Number,
    degree_plan: IDegreePlan[]
    // qualifiers: IQualifier[],
    rules: IRule[]
} 

/* This model represents a degree requirement rule. A rule has a Q object
    representing courses that can fulfill this rule and a number of required
    courses, number of required CUs, or both. */ 
export type IRule = {
    courses: ICourseQ[],
    min_num: Number,
    max_num: Number,
    min_cus: Number,
    max_cus: Number,
    requirement: string
}

/* Course model */
export type IQ = ICourse;

// [
//     {
//         "id": 1,
//         "name": "Computer Science, BSE",
//         "credits": 37,
//         "requirements": [
//             {
//                 "id": 2,
//                 "name": "Probability",
//                 "num": 1,
//                 "satisfied_by": 2,
//                 "topics": [
//                     "Topic 36424 (GPRD-9660 most recently)",
//                     "Topic 36433 (HCMG-0099 most recently)",
//                     "Topic 36432 (HCIN-6070 most recently)"
//                 ],
//                 "subrequirements": []
//             }
//         ]
//     }
// ]