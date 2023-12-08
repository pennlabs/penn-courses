export interface Degree {
  id: number;
  year: number;
  program: string;
  degree: string;
  major: string;
  concentration: string;
}

export interface DegreePlan {
  id: number;
  degree: Degree;
  degree_plan_id: number;
  name: string;
}

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