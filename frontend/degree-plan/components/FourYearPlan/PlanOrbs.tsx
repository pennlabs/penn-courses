import React from "react";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";

const MAX_ORBS = 4;
const OVERLAP = 0.45; // rem each circle tucks under the last
const SPREAD = 0.65; // rem each moves apart by when the row's actions show
const SKIPPED = new Set(["and", "of", "in", "the", "for", "to", "with"]);

type Program = NonNullable<DegreePlan["programs"]>[number];

/**
 * A program's initials, e.g. CS for Computer Science or AIB for AI for Business. A one-word
 * name takes its code's first letters instead, e.g. BIO for Biology.
 */
export const abbreviation = ({ name, code }: Program) => {
  const subject = name.replace(/^\w+ in /, "").replace(/\s*\(.*\)$/, "");
  const words = subject
    .split(/[^A-Za-z]+/)
    .filter((w) => w && !SKIPPED.has(w.toLowerCase()));
  if (words.length < 2) return code.slice(0, 3).toUpperCase();
  return words
    .map((word) =>
      word.length <= 3 && word === word.toUpperCase() ? word : word[0]
    )
    .join("")
    .toUpperCase()
    .slice(0, 3);
};

// Spread apart, the circles reach left of where they sat, so that much room is kept for them.
const Orbs = styled.span<{ $count: number }>`
  display: flex;
  flex-shrink: 0;
  padding-left: ${(props) => (props.$count - 1) * SPREAD}rem;

  & > * + * {
    margin-left: -${OVERLAP}rem;
  }

  & > * {
    transform: translateX(
      calc(var(--from-right) * var(--preview-open, 0) * -${SPREAD}rem)
    );
    transition: transform 0.2s ease;
  }

  @media (prefers-reduced-motion: reduce) {
    & > * {
      transition: none;
    }
  }
`;

const Orb = styled.span<{ $kind: string }>`
  position: relative;
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: ${(props) => `var(--program-${props.$kind}-bg)`};
  color: ${(props) => `var(--program-${props.$kind})`};
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: -0.02em;

  svg {
    position: absolute;
    inset: 0;
    transform: rotate(-90deg); /* the arc starts at the top */
  }
  .track {
    stroke: ${(props) => `var(--program-${props.$kind}-border)`};
  }
  .arc {
    stroke: ${(props) => `var(--program-${props.$kind})`};
  }
  span {
    position: relative;
  }
`;

// How far along a program is, as an arc around its abbreviation.
const Ring = ({ progress }: { progress: number }) => (
  <svg viewBox="0 0 36 36" aria-hidden>
    <circle
      className="track"
      cx="18"
      cy="18"
      r="16.5"
      fill="none"
      strokeWidth="3"
    />
    {progress > 0 && (
      <circle
        className="arc"
        cx="18"
        cy="18"
        r="16.5"
        fill="none"
        strokeWidth="3"
        strokeLinecap="round"
        pathLength={100}
        strokeDasharray={`${Math.min(progress, 1) * 100} 100`}
      />
    )}
  </svg>
);

const More = styled(Orb)`
  background: var(--primary-color-light);
  color: var(--primary-color-extra-dark);
  box-shadow: inset 0 0 0 1.5px var(--primary-color-dark);
`;

/** A ring per degree, major and minor of a plan, filled as far as it is complete. */
const PlanOrbs = ({ programs }: { programs: DegreePlan["programs"] }) => {
  if (!programs?.length) return null;
  const names = programs.map(
    (program) => `${program.name}: ${Math.round(program.progress * 100)}%`
  );
  const shown =
    programs.length > MAX_ORBS ? programs.slice(0, MAX_ORBS - 1) : programs;
  const count = shown.length + Number(shown.length < programs.length);
  // The rightmost circle stays put as the others spread out from it.
  const fromRight = (i: number) =>
    ({ "--from-right": count - 1 - i } as React.CSSProperties);
  return (
    <Orbs
      role="img"
      aria-label={names.join(", ")}
      title={names.join("\n")}
      $count={count}
    >
      {shown.map((program, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <Orb key={i} $kind={program.kind} style={fromRight(i)}>
          <Ring progress={program.progress} />
          <span>{abbreviation(program)}</span>
        </Orb>
      ))}
      {shown.length < programs.length && (
        <More $kind="degree" style={fromRight(count - 1)}>
          +{programs.length - shown.length}
        </More>
      )}
    </Orbs>
  );
};

export default PlanOrbs;
