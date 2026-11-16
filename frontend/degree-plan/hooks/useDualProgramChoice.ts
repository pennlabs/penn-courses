import { useEffect, useMemo, useRef, useState } from "react";
import { DualProgram } from "@/types";
import { SchoolSelection } from "@/utils/parseUtils";
import { matchingPrograms } from "@/utils/coordinatedProgram";

// The coordinated-program field. A transcript can set it before the majors are filled in,
// and that value stays, with the missing-degree error, until the majors fit it or leave a
// program that did fit. When the majors match exactly one program and the field is empty,
// that program is selected. Clearing it stays cleared until the majors change.
export const useDualProgramChoice = (
  programs: DualProgram[] | undefined,
  selections: SchoolSelection[],
  initialCode: string | null
) => {
  const [code, setCode] = useState<string | null>(initialCode);
  const cleared = useRef(false);
  const fitted = useRef(false);
  const selectionKey = selections
    .map((selection) => `${selection.school.value}:${selection.primary?.value.id ?? ""}`)
    .join("|");
  const previousKey = useRef(selectionKey);

  const matches = useMemo(
    () => (programs ? matchingPrograms(programs, selections) : []),
    // selectionKey already covers the primaries matchingPrograms reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [programs, selectionKey]
  );

  useEffect(() => {
    if (!programs) return;
    if (previousKey.current !== selectionKey) {
      cleared.current = false;
      previousKey.current = selectionKey;
    }
    const stillFits = code != null && matches.some((program) => program.code === code);
    if (code && !stillFits) {
      if (fitted.current) {
        fitted.current = false;
        setCode(null);
      }
      return;
    }
    if (stillFits) fitted.current = true;
    if (!code && !cleared.current && matches.length === 1) {
      fitted.current = true;
      setCode(matches[0].code);
    }
  }, [programs, selectionKey, code, matches]);

  const onChange = (program: DualProgram | undefined) => {
    if (!program) {
      cleared.current = true;
      fitted.current = false;
      setCode(null);
      return;
    }
    cleared.current = false;
    fitted.current = matches.some((match) => match.code === program.code);
    setCode(program.code);
  };

  return { code, onChange, matches };
};
