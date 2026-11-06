import { Cross2Icon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import { ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { PulseLoader } from "react-spinners";
import useSWR, { useSWRConfig } from "swr";
import { DegreeListing, DegreePlan, Fulfillment, Major, Minor, Options } from "@/types";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { deleteFetcher, postFetcher } from "@/hooks/swrcrud";
import { createMajorLabel } from "@/components/FourYearPlan/DegreeModal";
import {
  getLocalSemestersKey,
  interpolateSemesters,
  replacePlanSemesters,
} from "@/components/FourYearPlan/Semesters";
import { translateSemester } from "@/components/FourYearPlan/Semester";
import ToastContext from "@/components/Toast/Toast";
import {
  degreeCodeOf,
  majorOption,
  minorOption,
  SchoolSelection,
  takesAdditionalMajors,
} from "@/utils/parseUtils";
import { NextButton, schoolOptions, SecondaryButton } from "./SharedComponents";
import { color, FieldLabel } from "./onboardingStyles";
import {
  Body,
  Card,
  FieldError,
  Footer,
  Header,
  ScrollArea,
  ScrollContent,
  Section,
  Title,
} from "./formLayout";
import SchoolsField from "./SchoolsField";
import { placePrograms } from "./placePrograms";
import YearFields, { YearOption, yearOption, yearsInOrder } from "./YearFields";

const CloseButton = styled.button`
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 8px;
  background: none;
  color: ${color.muted};
  cursor: pointer;

  &:hover {
    background: rgba(61, 65, 119, 0.08);
    color: ${color.heading};
  }
`;

const PlanName = styled.p`
  margin: 0;
  font-size: 15px;
  color: ${color.muted};
`;

const Hint = styled.p`
  margin: 0;
  font-size: 13px;
  color: ${color.muted};
`;

const Chips = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
`;

const Chip = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 4px 4px 10px;
  border-radius: 6px;
  background: var(--primary-color-light);
  color: ${color.heading};
  font-size: 14px;

  button {
    display: grid;
    place-items: center;
    width: 22px;
    height: 22px;
    padding: 0;
    border: 0;
    border-radius: 4px;
    background: none;
    color: ${color.accent};
    cursor: pointer;
  }

  button:hover {
    background: rgba(61, 65, 119, 0.1);
    color: var(--error-color);
  }
`;

const Confirm = styled.div`
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: ${color.heading};

  ul {
    margin: 4px 0 0;
    padding-left: 1.2rem;
  }
`;

const SaveButton = styled(NextButton)`
  width: auto;
  min-width: 100px;
  padding: 0 1.25rem;
`;

const TRANSITION_MS = 200;

const Backdrop = styled.div<{ $shown: boolean }>`
  position: fixed;
  inset: 0;
  z-index: 9000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: rgba(32, 35, 74, 0.25);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  opacity: ${(props) => (props.$shown ? 1 : 0)};
  transition: opacity ${TRANSITION_MS}ms ease;

  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
`;

const Dialog = styled(Card)<{ $shown: boolean }>`
  position: relative;
  margin: 0;
  width: min(1000px, 100%);
  height: min(860px, 100%);
  border-radius: 16px;
  box-shadow: 0 24px 64px rgba(30, 32, 60, 0.25);
  outline: none;
  transform: ${(props) => (props.$shown ? "none" : "translateY(16px) scale(0.98)")};
  transition: transform ${TRANSITION_MS}ms ease;

  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
`;

// Escape and clicks outside close it only when `onDismiss` is given, so edits aren't lost by accident.
const ModalShell = ({
  shown,
  onDismiss,
  children,
}: {
  shown: boolean;
  onDismiss?: () => void;
  children: ReactNode;
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => dialogRef.current?.focus(), []);
  useEffect(() => {
    if (!onDismiss) return undefined;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onDismiss]);

  return (
    <Backdrop
      $shown={shown}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onDismiss?.();
      }}
    >
      <Dialog
        ref={dialogRef}
        $shown={shown}
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-programs-title"
        tabIndex={-1}
      >
        {children}
      </Dialog>
    </Backdrop>
  );
};

const readSemesterKeys = (planId: DegreePlan["id"]): string[] | null => {
  try {
    const stored = localStorage.getItem(getLocalSemestersKey(planId));
    return stored ? Object.keys(JSON.parse(stored)) : null;
  } catch {
    return null;
  }
};

// Fall of the first year through spring of the last, the way onboarding lays a plan out. Summer
// terms ("B") are left out: one at either end doesn't move the academic years.
const yearsOf = (keys: string[]) => {
  const terms = keys.filter((key) => /^\d{4}[AC]$/.test(key)).sort();
  if (!terms.length) return null;
  const first = terms[0];
  const last = terms[terms.length - 1];
  const year = (term: string) => Number(term.slice(0, 4));
  return {
    start: first.endsWith("C") ? year(first) : year(first) - 1,
    graduation: last.endsWith("A") ? year(last) : year(last) + 1,
  };
};

const placementsOf = (list: { degree: number | null }[] | undefined, key: "major" | "minor") =>
  new Map((list ?? []).map((row) => [(row as any)[key] as number, row.degree]));

// A plan's degrees as school cards, each with the majors and minors placed under it. One added
// before placement existed goes under the card for its own degree: a major names its degree in
// its code, and a minor doesn't, so it's only placed when the plan has a single degree.
const initialSelections = (plan: DegreePlan) => {
  const majorPlacements = placementsOf(plan.major_degrees, "major");
  const minorPlacements = placementsOf(plan.minor_degrees, "minor");
  const selections: SchoolSelection[] = plan.degrees.map((degree) => ({
    key: `degree-${degree.id}`,
    school: schoolOptions.find((o) => o.value === degree.degree) ?? {
      value: degree.degree,
      label: degree.degree,
    },
    primary: {
      value: degree as unknown as DegreeListing,
      label: createMajorLabel(degree as unknown as DegreeListing),
    },
    additional: [],
    minors: [],
  }));
  const cardFor = (degreeId: number | null | undefined) =>
    degreeId == null ? undefined : selections.find((s) => s.primary?.value.id === degreeId);

  const unplacedMajors: Major[] = [];
  plan.majors.forEach((major) => {
    const degreeId = majorPlacements.get(major.id);
    const card =
      cardFor(degreeId) ??
      (degreeId == null
        ? selections.find((s) => s.school.value === degreeCodeOf(major.program_code))
        : undefined);
    if (card) card.additional.push(majorOption(major, card.school));
    else unplacedMajors.push(major);
  });

  const unplacedMinors: Minor[] = [];
  plan.minors.forEach((minor) => {
    const degreeId = minorPlacements.get(minor.id);
    const card =
      cardFor(degreeId) ??
      (degreeId == null && selections.length === 1 ? selections[0] : undefined);
    // A card without a Minors field (a masters) would hide the minor, so it stays unplaced.
    if (card && takesAdditionalMajors(card.school)) card.minors!.push(minorOption(minor));
    else unplacedMinors.push(minor);
  });
  return { selections, unplacedMajors, unplacedMinors };
};

type EditProgramsPanelProps = {
  degreePlanId: DegreePlan["id"];
  onClose: () => void;
};

export default function EditProgramsPanel({ degreePlanId, onClose }: EditProgramsPanelProps) {
  const { data: plan } = useSWR<DegreePlan>(`/api/degree/degreeplans/${degreePlanId}`);
  const { data: fulfillments } = useSWR<Fulfillment[]>(
    `/api/degree/degreeplans/${degreePlanId}/fulfillments`
  );
  const { data: options } = useSWR<Options>("/api/options");

  const [shown, setShown] = useState(false);
  useEffect(() => {
    // Two frames, so the closed styles are painted before it transitions open.
    let frame = requestAnimationFrame(() => {
      frame = requestAnimationFrame(() => setShown(true));
    });
    return () => cancelAnimationFrame(frame);
  }, []);
  const close = useCallback(() => {
    setShown(false);
    setTimeout(onClose, TRANSITION_MS);
  }, [onClose]);

  if (!plan || !fulfillments || !options) {
    return (
      <ModalShell shown={shown} onDismiss={close}>
        <div style={{ margin: "auto" }}>
          <PulseLoader size={10} color="var(--primary-color-xx-dark)" />
        </div>
      </ModalShell>
    );
  }
  return (
    <EditProgramsForm
      plan={plan}
      fulfillments={fulfillments}
      currentYear={Number(options.SEMESTER.slice(0, 4))}
      shown={shown}
      onClose={close}
    />
  );
}

type EditProgramsFormProps = {
  plan: DegreePlan;
  fulfillments: Fulfillment[];
  currentYear: number;
  shown: boolean;
  onClose: () => void;
};

function EditProgramsForm({
  plan,
  fulfillments,
  currentYear,
  shown,
  onClose,
}: EditProgramsFormProps) {
  const { mutate } = useSWRConfig();
  const showToast = useContext(ToastContext);

  const { data: degrees, isLoading: isLoadingDegrees } =
    useSWR<DegreeListing[]>("/api/degree/degrees");
  const { data: standaloneMajors, isLoading: isLoadingMajors } =
    useSWR<Major[]>("/api/degree/majors");
  const { data: minors, isLoading: isLoadingMinors } = useSWR<Minor[]>("/api/degree/minors");

  const initial = useMemo(() => {
    const semesterKeys = readSemesterKeys(plan.id);
    // With nothing stored, the plan view shows four years from now.
    const years = (semesterKeys && yearsOf(semesterKeys)) ?? {
      start: currentYear,
      graduation: currentYear + 4,
    };
    return { ...initialSelections(plan), semesterKeys, years };
  }, [plan, currentYear]);

  const [selections, setSelections] = useState(initial.selections);
  const [unplacedMajors, setUnplacedMajors] = useState(initial.unplacedMajors);
  const [unplacedMinors, setUnplacedMinors] = useState(initial.unplacedMinors);
  const [startingYear, setStartingYear] = useState<YearOption | null>(
    yearOption(initial.years.start)
  );
  const [graduationYear, setGraduationYear] = useState<YearOption | null>(
    yearOption(initial.years.graduation)
  );
  const [confirming, setConfirming] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const yearChoices = (around: number[], kept: number) =>
    [...new Set([...around, kept])].sort((a, b) => a - b).map(yearOption);
  const startYearOptions = yearChoices(
    [...Array(5).keys()].map((i) => currentYear - i),
    initial.years.start
  );
  const graduationYearOptions = yearChoices(
    [...Array(5).keys()].map((i) => currentYear + i),
    initial.years.graduation
  );

  // What saving would change, worked out against the plan as it was loaded.
  const changes = useMemo(() => {
    const oldDegrees = new Set(plan.degrees.map((d) => d.id));
    const newDegrees = new Set(
      selections.flatMap((s) => (s.primary ? [s.primary.value.id] : []))
    );

    const oldMajorPlacement = placementsOf(plan.major_degrees, "major");
    const oldMinorPlacement = placementsOf(plan.minor_degrees, "minor");
    const keptMajors = new Set([
      ...unplacedMajors.map((m) => m.id),
      ...selections.flatMap((s) => s.additional.map((m) => m.value.id)),
    ]);
    const keptMinors = new Set([
      ...unplacedMinors.map((m) => m.id),
      ...selections.flatMap((s) => (s.minors ?? []).map((m) => m.value.id)),
    ]);
    // Where the editor opened with each one, including placements it filled in itself.
    const shownAt = (pick: (s: SchoolSelection) => { value: { id: number } }[]) =>
      new Map(
        initial.selections.flatMap((s) => pick(s).map((m) => [m.value.id, s.primary?.value.id]))
      );
    const shownMajors = shownAt((s) => s.additional);
    const shownMinors = shownAt((s) => s.minors ?? []);
    const editedPlacement = selections.some(
      (s) =>
        s.additional.some((m) => shownMajors.get(m.value.id) !== s.primary?.value.id) ||
        (s.minors ?? []).some((m) => shownMinors.get(m.value.id) !== s.primary?.value.id)
    );

    // The ones new to the plan or moving to this card's degree.
    const moved = (ids: number[], old: Map<number, number | null>, degreeId?: number) =>
      ids.filter((id) => !old.has(id) || old.get(id) !== degreeId);

    let semesterKeys: string[] | null = null;
    let movedToDock: Fulfillment[] = [];
    const yearsChanged =
      startingYear?.value !== initial.years.start ||
      graduationYear?.value !== initial.years.graduation;
    if (yearsChanged && startingYear && graduationYear) {
      const first = `${startingYear.value}C`;
      const last = `${graduationYear.value}A`;
      const kept = (initial.semesterKeys ?? []).filter(
        (key) => key === TRANSFER_CREDIT_SEMESTER_KEY || (key >= first && key <= last)
      );
      semesterKeys = [
        ...new Set([
          TRANSFER_CREDIT_SEMESTER_KEY,
          ...kept,
          ...Object.keys(interpolateSemesters(startingYear.value, graduationYear.value)),
        ]),
      ];
      const keep = new Set(semesterKeys);
      movedToDock = fulfillments.filter((f) => f.semester && !keep.has(f.semester));
    }

    return {
      removedDegrees: plan.degrees.filter((d) => !newDegrees.has(d.id)),
      addedDegrees: [...newDegrees].filter((id) => !oldDegrees.has(id)),
      editedPlacement,
      removedMajors: plan.majors.filter((m) => !keptMajors.has(m.id)),
      removedMinors: plan.minors.filter((m) => !keptMinors.has(m.id)),
      placed: selections.map((s) => ({
        degreeId: s.primary?.value.id,
        majorIds: moved(
          s.additional.map((m) => m.value.id),
          oldMajorPlacement,
          s.primary?.value.id
        ),
        minorIds: moved(
          (s.minors ?? []).map((m) => m.value.id),
          oldMinorPlacement,
          s.primary?.value.id
        ),
      })),
      semesterKeys,
      movedToDock,
    };
  }, [
    plan,
    fulfillments,
    selections,
    unplacedMajors,
    unplacedMinors,
    startingYear,
    graduationYear,
    initial,
  ]);

  const removals = [
    ...changes.removedDegrees.map((d) => `${d.degree} in ${d.major_name}`),
    ...changes.removedMajors.map((m) => m.name ?? m.code),
    ...changes.removedMinors.map((m) => m.name ?? `${m.code} minor`),
  ];
  const changed =
    removals.length > 0 ||
    changes.addedDegrees.length > 0 ||
    changes.editedPlacement ||
    changes.semesterKeys !== null;
  const complete =
    selections.every((s) => s.primary) && yearsInOrder(startingYear, graduationYear);

  const save = async () => {
    setSaving(true);
    setError(null);
    const base = `/api/degree/degreeplans/${plan.id}`;
    try {
      if (changes.removedDegrees.length)
        await deleteFetcher(`${base}/degrees`, {
          degree_ids: changes.removedDegrees.map((d) => d.id),
        });
      if (changes.addedDegrees.length)
        await postFetcher(`${base}/degrees`, { degree_ids: changes.addedDegrees });
      if (changes.removedMajors.length)
        await deleteFetcher(`${base}/majors`, {
          major_ids: changes.removedMajors.map((m) => m.id),
        });
      if (changes.removedMinors.length)
        await deleteFetcher(`${base}/minors`, {
          minor_ids: changes.removedMinors.map((m) => m.id),
        });
      await placePrograms(plan.id, changes.placed);

      for (const fulfillment of changes.movedToDock) {
        // eslint-disable-next-line no-await-in-loop
        await deleteFetcher(`${base}/fulfillments/${fulfillment.full_code}`);
        // eslint-disable-next-line no-await-in-loop
        await postFetcher("/api/degree/docked", { full_code: fulfillment.full_code });
      }
      if (changes.semesterKeys) replacePlanSemesters(plan.id, changes.semesterKeys);

      await Promise.all([
        mutate(base),
        mutate(`${base}/fulfillments`),
        mutate("/api/degree/docked"),
      ]);
      showToast(`Saved changes to ${plan.name}`, false);
      onClose();
    } catch {
      setError("Some changes couldn't be saved. Check your programs and try again.");
      setConfirming(false);
      setSaving(false);
      // Whatever did save should show when the editor reopens.
      mutate(base);
      mutate(`${base}/fulfillments`);
    }
  };

  const needsConfirm = removals.length > 0 || changes.movedToDock.length > 0;

  return (
    <ModalShell shown={shown} onDismiss={changed || saving ? undefined : onClose}>
        <CloseButton type="button" aria-label="Close" onClick={onClose} disabled={saving}>
          <Cross2Icon width={18} height={18} />
        </CloseButton>
        <ScrollArea>
          <ScrollContent>
            <Header>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <Title id="edit-programs-title">Edit your programs</Title>
                <PlanName>{plan.name}</PlanName>
              </div>
            </Header>

            <Body>
              <Section>
                <YearFields
                  idPrefix="edit"
                  startOptions={startYearOptions}
                  graduationOptions={graduationYearOptions}
                  startingYear={startingYear}
                  graduationYear={graduationYear}
                  setStartingYear={setStartingYear}
                  setGraduationYear={setGraduationYear}
                />
                {changes.movedToDock.length > 0 && (
                  <Hint>
                    {changes.movedToDock.length} planned{" "}
                    {changes.movedToDock.length === 1 ? "course falls" : "courses fall"} outside
                    these years and will move to your dock.
                  </Hint>
                )}
              </Section>

              <Section>
                <FieldLabel as="div">Schools, majors &amp; minors</FieldLabel>
                <SchoolsField
                  selections={selections}
                  setSelections={setSelections}
                  degrees={degrees}
                  standaloneMajors={standaloneMajors}
                  minors={minors}
                  unavailableMinorIds={unplacedMinors.map((m) => m.id)}
                  isLoadingDegrees={isLoadingDegrees}
                  isLoadingMajors={isLoadingMajors}
                  isLoadingMinors={isLoadingMinors}
                />
              </Section>

              {unplacedMajors.length + unplacedMinors.length > 0 && (
                <Section>
                  <FieldLabel as="div">Not under a degree</FieldLabel>
                  <Hint>
                    These aren&apos;t part of any degree in this plan, so they only share courses
                    the way their audits allow. Remove one here and add it under a school to place
                    it.
                  </Hint>
                  <Chips>
                    {unplacedMajors.map((major) => (
                      <Chip key={`major-${major.id}`}>
                        {`${major.name ?? major.code} (${major.year}, ${degreeCodeOf(
                          major.program_code
                        )})`}
                        <button
                          type="button"
                          aria-label={`Remove ${major.name ?? major.code}`}
                          onClick={() =>
                            setUnplacedMajors((current) => current.filter((m) => m !== major))
                          }
                        >
                          <Cross2Icon width={14} height={14} />
                        </button>
                      </Chip>
                    ))}
                    {unplacedMinors.map((minor) => (
                      <Chip key={`minor-${minor.id}`}>
                        {minorOption(minor).label}
                        <button
                          type="button"
                          aria-label={`Remove ${minor.name ?? minor.code}`}
                          onClick={() =>
                            setUnplacedMinors((current) => current.filter((m) => m !== minor))
                          }
                        >
                          <Cross2Icon width={14} height={14} />
                        </button>
                      </Chip>
                    ))}
                  </Chips>
                </Section>
              )}
            </Body>
          </ScrollContent>
        </ScrollArea>

        <Footer>
          {confirming ? (
            <Confirm role="alert">
              {removals.length > 0 && (
                <>
                  Saving removes:
                  <ul>
                    {removals.map((removal) => (
                      <li key={removal}>{removal}</li>
                    ))}
                  </ul>
                </>
              )}
              {changes.movedToDock.length > 0 && (
                <div>
                  {changes.movedToDock.length} courses in{" "}
                  {[...new Set(changes.movedToDock.map((f) => translateSemester(f.semester!)))].join(", ")}{" "}
                  move to your dock.
                </div>
              )}
            </Confirm>
          ) : (
            error && <FieldError role="alert" style={{ flex: 1 }}>{error}</FieldError>
          )}
          <SecondaryButton
            type="button"
            onClick={() => (confirming ? setConfirming(false) : onClose())}
            disabled={saving}
          >
            {confirming ? "Keep editing" : "Cancel"}
          </SecondaryButton>
          <SaveButton
            onClick={() => (needsConfirm && !confirming ? setConfirming(true) : save())}
            disabled={!changed || !complete || saving}
          >
            {saving && <PulseLoader size={8} color="white" />}
            {!saving && (confirming ? "Save changes" : "Save")}
          </SaveButton>
        </Footer>
    </ModalShell>
  );
}
