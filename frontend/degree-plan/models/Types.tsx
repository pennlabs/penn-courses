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
    note: string
}

enum QualifierType {
    GPA = "GPA",
    CUS = "CUS",
    NUM = "NUM"
}

export type IRule = {
    num: Number,
    nax_num: Number,
    cus: Number,
    max_cus: Number
}

export type IQualifier = {
    label: string,
    code: string,
    num: Number,
    type: QualifierType
}

export type IReq = {
    name: string,
    code: string,
    qualifiers: IQualifier[],
    rules: IRule[]
} 

export type IDegreePlan = {
    program: string,
    degree: string,
    major: string,
    concentration: string,
    year: Number
}


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