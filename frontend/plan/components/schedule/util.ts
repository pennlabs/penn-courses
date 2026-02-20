import { Day, Weekdays, Weekends } from "../../types";

export const dayMap: { [key: number]: Day | null } = {
  0: Weekends.U, // Sunday
  1: Weekdays.M, // Monday
  2: Weekdays.T, // Tuesday
  3: Weekdays.W, // Wednesday
  4: Weekdays.R, // Thursday
  5: Weekdays.F, // Friday
  6: Weekends.S, // Saturday
}