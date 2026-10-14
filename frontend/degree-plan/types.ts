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

export interface DualProgram {
  code: string;
  name: string;
  left_programs: string[];
  right_programs: string[];
  left_allowed_majors: string[];
  right_allowed_majors: string[];
  left_variant: string | null;
  right_variant: string | null;
  cu_floor: number | null;
  max_shared_cu: number | null;
}

/** One slice of a plan after dual-degree composition: a degree, a major block, or shared College requirements. */
export interface PlanComponent {
  key: string;
  relation: "degrees" | "majors" | "minors" | "college" | "degree-major";
  id: number | null;
  role: string;
  title: string;
  year: number | null;
  program: string | null;
  removable: boolean;
  rules: Rule[];
}

export interface PlanViolation {
  full_code: string;
  kind: "too_many_degrees" | "undergrad_grad_cu" | "grad_grad" | "also_offered" | "mutually_exclusive";
  components: string[];
  message?: string;
}

export interface PlanSummary {
  kind: string;
  dual_program: { code: string; name: string } | null;
  course_claims: { [fullCode: string]: string[] };
  violations: PlanViolation[];
  cas: {
    floor: number;
    major_cu: number;
    shared_cu: number;
    remaining: number;
  } | null;
}

export interface DegreePlan extends DBObject {
  id: number;
  degrees: Degree[]
  /** Majors pursued beyond the one this plan's degree already includes. */
  majors: Major[]
  minors: Minor[]
  dual_program?: DualProgram | null;
  right_variant?: string | null;
  components?: PlanComponent[];
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
  /** True when the course was read from a transcript. Otherwise it was added on the plan. */
  from_transcript?: boolean;
}

// Internal representation of a plan (this is derived from fulfillments)
export interface Semester {
  semester: string;
  courses: string[];
}

export interface GeneratedPlacement {
  slot_ids: string[];
  kind: "course" | "placeholder" | "placement";
  full_code: string | null;
  fulfillment_id: number | null;
  label: string;
  /** Compact schedule code, such as `ESE 2000+` or `CIS 1100/CIS 1200 (+3)`. */
  short_label?: string;
  cu: number;
  semester: string;
  alternatives: string[];
  rules: number[];
  rule_q: string | null;
  /** Two open slots, one card. alternatives are courses that could fill both. */
  overlap?: boolean;
}

export interface GenerateResponse {
  placements: GeneratedPlacement[];
  semesters: { key: string; synthetic: boolean }[];
  unplaced: { slot_id: string | null; full_code: string | null; reason: string }[];
  open_rule_count: number;
  generated_cu: number;
  course_claims?: { [fullCode: string]: string[] };
  violations?: PlanViolation[];
  claims_updated?: boolean;
}

export interface SemesterGenConfig {
  cuCap: number;
  gap: boolean;
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
