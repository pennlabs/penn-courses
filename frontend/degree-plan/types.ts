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
  // False when the rule's audit block takes no AP, IB or transfer credit, e.g. the College's
  // Foundations. A course filed under TRANSFER_CREDIT_SEMESTER_KEY cannot be dropped on it.
  transfer_credit_allowed: boolean;
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
  credits: number;
}

/** A major or minor added on top of a degree, carrying only its own block's rules. */
export interface ProgramComponent extends DBObject {
  id: number;
  program_code: string;
  code: string;
  name: string | null;
  year: number;
  credits: number | null;
  rules: Rule[];
}

export interface Major extends ProgramComponent {
  concentration: string | null;
  concentration_name: string | null;
}

export interface Minor extends ProgramComponent {}

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
  /** Majors pursued beyond the one this plan's degree already includes. */
  majors: Major[]
  minors: Minor[]
  /** Which of the plan's degrees each major was added under; null when it wasn't placed. */
  major_degrees?: { major: Major["id"]; degree: Degree["id"] | null }[];
  /** Which of the plan's degrees each minor was added under; null when it wasn't placed. */
  minor_degrees?: { minor: Minor["id"]; degree: Degree["id"] | null }[];
  /** The coordinated program (e.g. M&T) two of the plan's degrees make up, if any. */
  dual_program?: DualProgram | null;
  /** Code of the variant chosen for the program's right side, when it isn't the default. */
  right_variant?: string | null;
  /** Each degree, major and minor as the plan applies it, e.g. with M&T's changes made. */
  components?: PlanComponent[];
  name: string;
  updated_at: string;
  created_at: string;
}

/** A plan's degree, major or minor with any coordinated program's changes to its rules. */
export interface PlanComponent {
  key: string;
  relation: string;
  id: number;
  rules: Rule[];
}

/** A coordinated program pairing a degree from each of two schools, e.g. M&T. */
export interface DualProgram {
  code: string;
  name: string;
  /** Degree programs (e.g. "EU_BSE") that can fill each side. */
  left_programs: string[];
  right_programs: string[];
  /** Majors a side is limited to; empty when any major may fill it. */
  left_allowed_majors: string[];
  right_allowed_majors: string[];
  left_variant: string | null;
  right_variant: string | null;
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
  attribute_codes: string[];
}

// The interface we use with React DND
export interface DnDCourse {
  full_code: string;
  semester?: string | null; // present when the item is a fulfillment dragged from the plan
  rules?: number[];
  rule_id?: number // only used when dragging from REQ panel
  unselected_rules?: number[];
  fulfillment?: Fulfillment;
  course?: Course | null;
}

export interface Fulfillment extends DBObject {
  course: Course | null; // id
  semester: string | null;
  rules: number[]; // ids
  id: number;
  degree_plan: number; // id
  full_code: string;
  unselected_rules: number[];
  overrides: number[]; // rule IDs manually overridden to count for
  legal: boolean;
  // For a submatriculant, which transcript record listed the course: their bachelors, their
  // masters, or both (double counted). Null for a course added by hand.
  level: "UNDERGRADUATE" | "GRADUATE" | "SHARED" | null;
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