export interface DBObject {
  id: any;
}

export interface Rule extends DBObject {
  id: number;
  q: string; // could be blank
  q_json: any;
  title: string; // could be blank
  credits: number | null;
  parent: Rule["id"],
  num: number | null;
  concentration: string;
  rules: Rule[];
}

/** Onboarding page types */
export interface SchoolOption {
  label: DegreeListing["degree"];
  value: DegreeListing["degree"];
}

export interface MajorOption {
  label: DegreeListing["major"];
  value: DegreeListing;
}

export interface DegreeListing extends DBObject {
  id: number;
  year: number;
  program: string;
  degree: string;
  major: string;
  major_name: string;
  concentration: string;
  concentration_name: string;
  rules: number[];
  credits: number;
}

export interface DockedCourse extends DBObject {
  id: number;
  full_code: string;
  person?: any;
}


export interface Degree extends DBObject {
  id: number;
  year: number;
  program: string;
  degree: string;
  major: string;
  major_name: string;
  concentration: string;
  concentration_name: string;
  rules: Rule[];
}

export interface DegreePlan extends DBObject {
  id: number;
  degrees: Degree[]
  name: string;
  updated_at: string;
  created_at: string;
}

// TODO: this is pulled from alert, we should move it to a shared location
export interface Profile {
    email: string | null;
    phone: string | null;
}

export interface User {
    username: string;
    first_name: string;
    last_name: string;
    profile: Profile;
}

export interface Options {
  RECRUITING: string;
  SEMESTER:  string;
  REGISTRATION_OPEN: boolean;
  SEND_FROM_WEBHOOK: boolean;
}

// TODO: differentiate between course and course detail
export interface Course {
  title: string;
  id: string;
  description: string;
  semester: string;
  instructor_quality: number;
  course_quality: number;
  work_required: number;
  difficulty: number;
  credits: number;
}

// The interface we use with React DND
export interface DnDCourse {
  full_code: string;
  rules?: number[];
  rule_id?: number // only used when dragging from REQ panel
  unselected_rules?: number[];
  fulfillment?: Fulfillment;
}

export interface Fulfillment extends DBObject {
  course: Course | null; // id
  semester: string | null;
  rules: number[]; // ids
  id: number;
  degree_plan: number; // id
  full_code: string;
  unselected_rules: number[];
}

// Internal representation of a plan (this is derived from fulfillments)
export interface Semester {
  semester: string;
  courses: string[];
}

export function assertValueType<T, K extends keyof T>(obj: T, idKey: K, value: any): asserts value is T[K] {
    if (obj[idKey] !== value) {
        // throw new Error(`Value ${value} is not of type ${typeof obj[idKey]}`);
    }
}

export interface PromiseConstructor {
  withResolvers<T>(): {
    promise: Promise<T>
    resolve: (value: T | PromiseLike<T>) => void
    reject: (reason?: any) => void
  }
 }