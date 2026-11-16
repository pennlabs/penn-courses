import { DualProgram } from "@/types";
import { SchoolSelection } from "@/utils/parseUtils";
import { programSides } from "@/components/OnboardingPanels/DualProgramField";

// The coordinated programs whose two sides the current primary majors already fill.
// A pair matches at most one: the allowed majors do not overlap on the same two schools.
export const matchingPrograms = (
  programs: DualProgram[],
  selections: SchoolSelection[]
): DualProgram[] =>
  programs.filter((program) => {
    const sides = programSides(program, selections);
    return Boolean(sides.left && sides.right);
  });

// Non-College duals plan five academic years. Every coordinated program is one, and so is
// an uncoordinated pair of schools once the student has chosen the program. College-only
// plans stay at four.
export const degreeSpan = (dual: boolean) => (dual ? 5 : 4);
