export interface DBObject {
  id: any;
}

export interface Degree extends DBObject {
  id: number;
  year: number;
  program: string;
  degree: string;
  major: string;
  concentration: string;
}

export interface DegreePlan extends DBObject {
  id: number;
  degree: Degree;
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