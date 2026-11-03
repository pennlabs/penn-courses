import { DegreeListing } from "@/types";

// The backend's programs for the Jerome Fisher Program in Management & Technology (M&T). An M&T
// student's degrees are separate M&T versions of the Wharton and SEAS degrees, and one without a
// Wharton concentration has a Wharton degree of their own (see degree.utils.mt_degrees).
export const MT_PROGRAMS = new Set(["EU_BSE_MANT", "EU_BAS_MANT", "WU_BS_MANT", "WU_BS_MAT_U"]);
export const MT_UNDECLARED_PROGRAM = "WU_BS_MAT_U";

// The ordinary programs that M&T has its own versions of.
const PROGRAMS_WITH_MT_VERSIONS = new Set(["EU_BSE", "EU_BAS", "WU_BS"]);

export const isMandTDegree = (degree: Pick<DegreeListing, "program">) =>
  MT_PROGRAMS.has(degree.program);

// Whether a degree belongs among the options for an M&T student (or for anyone else). An M&T
// student takes the M&T version of a Wharton or SEAS degree rather than the ordinary one, but
// may still hold degrees M&T has no version of, such as a submatriculant's masters.
export const suitsMandT = (degree: Pick<DegreeListing, "program">, mandT: boolean) =>
  mandT ? !PROGRAMS_WITH_MT_VERSIONS.has(degree.program) : !isMandTDegree(degree);
