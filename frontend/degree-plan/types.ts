export interface DBObject {
  id: any;
}

export interface Rule extends DBObject {
  id: number;
  q: string; // could be blank
  title: string; // could be blank
  credits: number | null;
  parent: Rule["id"],
  num: number | null;
  concentration: string;
  rules: Rule[];
}

export interface Degree extends DBObject {
  id: number;
  year: number;
  program: string;
  degree: string;
  major: string;
  concentration: string;
  rules: Rule[];
}

export interface DegreePlan extends DBObject {
  id: number;
  degrees: Degree[];
  degree_ids: number[]; // the ids of the degrees in the degree plan, which we use to mutate the degree plan
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
  id: number;
  name: string;
  full_code: string;
  description: string;
  semester: string;
}

export interface Fulfillment extends DBObject {
  id: number;
  degree_plan: number; // id
  full_code: string;
  historical_course: Course; // id
  semester: string | null;
  rules: number[]; // ids
}

// Internal representation of a plan (this is derived from fulfillments)
export interface Semester {
  semester: string;
  courses: string[];
}