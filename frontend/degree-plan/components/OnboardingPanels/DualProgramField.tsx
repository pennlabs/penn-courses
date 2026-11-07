import styled from "@emotion/styled";
import Select from "react-select";
import { DegreeListing, DualProgram } from "@/types";
import { SchoolSelection } from "@/utils/parseUtils";
import {
  color,
  Field,
  FieldLabel,
  Optional,
  selectStyles,
} from "./onboardingStyles";
import { FieldError } from "./formLayout";

const PROGRAM_LABELS: { [program: string]: string } = {
  EU_BSE: "Engineering BSE",
  EU_BAS: "Engineering BAS",
  WU_BS: "Wharton BS",
  AU_BA: "College BA",
};

const Hint = styled.p`
  margin: 0;
  font-size: 13px;
  color: ${color.muted};
`;

type Side = "left" | "right";

// The degree on each side of a program: the first school card whose degree the side accepts.
export const programSides = (
  program: DualProgram,
  selections: SchoolSelection[]
) => {
  const fill = (side: Side) =>
    selections.find(({ primary }) => {
      if (!primary) return false;
      const allowed = program[`${side}_allowed_majors`];
      return (
        program[`${side}_programs`].includes(primary.value.program) &&
        (!allowed.length || allowed.includes(primary.value.major))
      );
    })?.primary?.value;
  return { left: fill("left"), right: fill("right") };
};

// e.g. "a College BA in International Studies" or "an Engineering BSE or Engineering BAS".
const describeSide = (
  program: DualProgram,
  side: Side,
  degrees: DegreeListing[] | undefined
) => {
  const schools = program[`${side}_programs`].map(
    (code) => PROGRAM_LABELS[code] ?? code
  );
  const majors = program[`${side}_allowed_majors`].map(
    (major) => degrees?.find((d) => d.major === major)?.major_name ?? major
  );
  const school = schools.join(" or ");
  const article = /^[AEIOU]/.test(school) ? "an" : "a";
  return `${article} ${school}${
    majors.length ? ` in ${majors.join(" or ")}` : ""
  }`;
};

// What's wrong with the program as chosen, or null when both of its sides are filled.
export const programError = (
  program: DualProgram | undefined,
  selections: SchoolSelection[],
  degrees: DegreeListing[] | undefined
) => {
  if (!program) return null;
  const sides = programSides(program, selections);
  const missing = (["left", "right"] as Side[]).filter((side) => !sides[side]);
  if (!missing.length) return null;
  return `${program.name} needs ${missing
    .map((side) => describeSide(program, side, degrees))
    .join(" and ")}. Add it under your schools below.`;
};

type DualProgramFieldProps = {
  programs: DualProgram[] | undefined;
  isLoading: boolean;
  value: DualProgram | undefined;
  onChange: (program: DualProgram | undefined) => void;
  selections: SchoolSelection[];
  degrees: DegreeListing[] | undefined;
};

export default function DualProgramField({
  programs,
  isLoading,
  value,
  onChange,
  selections,
  degrees,
}: DualProgramFieldProps) {
  const error = programError(value, selections, degrees);
  const sides = value && programSides(value, selections);

  return (
    <Field>
      <FieldLabel htmlFor="dual-program">
        Coordinated program
        <Optional />
      </FieldLabel>
      <Select
        inputId="dual-program"
        options={programs ?? []}
        value={value ?? null}
        onChange={(selected) => onChange(selected ?? undefined)}
        getOptionLabel={(program) => program.name}
        getOptionValue={(program) => program.code}
        isClearable
        isLoading={isLoading}
        placeholder="None"
        styles={selectStyles}
        menuPortalTarget={
          typeof document !== "undefined" ? document.body : null
        }
      />
      {error && <FieldError role="alert">{error}</FieldError>}
      {!error && sides?.left && sides.right && (
        <Hint>
          Pairs your {PROGRAM_LABELS[sides.left.program] ?? sides.left.degree}{" "}
          and {PROGRAM_LABELS[sides.right.program] ?? sides.right.degree}{" "}
          degrees.
        </Hint>
      )}
    </Field>
  );
}
