import FlexSemester, { SkeletonSemester } from "./Semester";
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import { Course, DegreePlan, Fulfillment, GeneratedPlacement, SemesterGenConfig } from "@/types";
import useSWR from "swr";
import React, { useEffect, useRef, useState, useCallback } from "react";
import Select from "react-select";
import { ModalKey } from "./DegreeModal";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";

const getNextSemester = (semester: string) => {
  const year = parseInt(semester.slice(0, 4));
  const season = semester.slice(4);
  if (season === "A") {
    // Spring -> Fall
    return `${year}C`;
  } else if (season === "B") {
    // Summer -> Fall
    return `${year}C`;
  } else {
    // Fall -> Spring
    return `${year + 1}A`;
  }
};

export const getLocalSemestersKey = (degreeplanId: DegreePlan["id"]) =>
  `PDP-${degreeplanId}-semesters`;

const YEAR_NAMES = ["Freshman", "Sophomore", "Junior", "Senior"];
const SEASONS = [
  { code: "C", label: "Fall" },
  { code: "A", label: "Spring" },
  { code: "B", label: "Summer" },
] as const;

const isTermKey = (key: string) => /^\d{4}[ABC]$/.test(key);

/** Fall starts an academic year; the following spring and summer belong to it. */
const academicYear = (key: string) => {
  const year = Number(key.slice(0, 4));
  return key.endsWith("C") ? year : year - 1;
};

const termKey = (academic: number, season: string) =>
  season === "C" ? `${academic}C` : `${academic + 1}${season}`;

const yearName = (index: number) => YEAR_NAMES[index] ?? `Year ${index + 1}`;

const transferCollapsedKey = (degreeplanId: DegreePlan["id"]) =>
  `PDP-${degreeplanId}-transfer-collapsed`;

const collapsedYearsKey = (degreeplanId: DegreePlan["id"]) =>
  `PDP-${degreeplanId}-collapsed-years`;

const SemestersContainer = styled.div`
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1.25rem;
`;

const YearSection = styled.section`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const YearLabel = styled.button`
  display: flex;
  align-items: center;
  gap: 0.45rem;
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7280;
  cursor: pointer;

  i {
    width: 0.7rem;
  }
`;

const YearSummary = styled.span`
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
`;

const YearGrid = styled.div<{ $columns: number }>`
  display: grid;
  grid-template-columns: repeat(${(props) => props.$columns}, minmax(0, 1fr));
  gap: 1.25rem;
  align-items: stretch;
`;

const EmptyTerm = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  min-height: 6rem;
  border: 2px dashed rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  background: transparent;
  color: #9ca3af;
  font: inherit;
  font-weight: 600;
  cursor: pointer;

  &:hover {
    color: var(--plus-button-color);
    border-color: var(--plus-button-color);
  }
`;

const AddSemesterContainer = styled.div`
  background: #ffffff;
  border-style: dashed;
  border-radius: 10px;
  border-width: 2px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  flex: 1 1 15rem;
  align-items: center;
  color: var(--plus-button-color);
`;

const AddButtonContainer = styled.div`
  height: 100%;
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  align-items: center;
  color: var(--plus-button-color);
`;

const PlusIcon = styled(Icon)`
  width: 100%;
  align-items: center;
`;

const AddButton = styled.div`
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const YearInput = styled.input`
  width: 9rem;
  background-color: transparent;
  border-color: #9FB5EF;
  color: #C1C1C1;
  box-shadow: none;
  &:hover {
    borderColor: "#9FB5EF";
  }

  padding: .75rem;
  padding-top: .5rem;
  padding-bottom: .5rem;
  border-style: solid;
  border-radius: .25rem;
  border-width: 1px;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  font-size: var(--type-body);
`

const selectStyles = (topOrBottom: boolean) => ({
  control: (provided: any) => ({
    ...provided,
    width: "9rem",
    backgroundColor: "transparent",
    borderColor: "#9FB5EF",
    color: "#C1C1C1",
    boxShadow: "none",
    "&:hover": {
      borderColor: "#9FB5EF",
    },
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
    borderBottom: 0
  }),
  singleValue: (provided: any) => ({
    ...provided,
    color: "#C1C1C1",
  }),
});

// TODO: get a consistent color palette across PCx
interface ModifySemestersProps {
  addSemester: (semester: Course["semester"]) => void;
  className?: string;
  semesters: { [semester: string]: Fulfillment[] };
}

const ModifySemesters = ({
  addSemester,
  semesters,
  className,
}: ModifySemestersProps) => {
  const latestSemester =
    Object.keys(semesters).filter(isTermKey).sort((a, b) => a.localeCompare(b)).pop() || "2026A"; // TODO: Change fallback value to start semester (based on onboarding?)

  const nextSemester = getNextSemester(latestSemester);
  const [nextYear, nextSeason] = [
    nextSemester.slice(0, 4),
    nextSemester.slice(4),
  ];

  const [selectedYear, setSelectedYear] = useState(nextYear);
  const [selectedSeason, setSelectedSeason] = useState(nextSeason);

  const semesterKeys = Object.keys(semesters).sort();

  const handleAddSemester = () => {
    const semester = `${selectedYear}${selectedSeason}`;
    addSemester(semester);
  };

  const seasonOptions = [
    { value: "A", label: "Spring" },
    { value: "B", label: "Summer" },
    { value: "C", label: "Fall" },
  ];

  return (
    // TODO: add a modal for this
    <AddSemesterContainer className={className}>
      <AddButtonContainer role="button" onClick={handleAddSemester}>
        <AddButton>
          <PlusIcon>
            <i className="fas fa-plus fa-lg"></i>
          </PlusIcon>
          <div>Add Semester</div>
        </AddButton>
      </AddButtonContainer>

      <Select
        styles={selectStyles(true)}
        options={seasonOptions}
        value={seasonOptions.find((option) => option.value === selectedSeason)}
        onChange={(option) => setSelectedSeason(option ? option.value : selectedSeason)}
      />

      <YearInput
        value={selectedYear}
        type="number"
        onChange={(e) => setSelectedYear(e.target.value)}
      />
    </AddSemesterContainer>
  );
};

export const interpolateSemesters = (startingYear: number, graduationYear: number) => {
  let res = {} as { [semester: string]: Fulfillment[] };
  for (let year = startingYear; year < graduationYear; year++) {
    res[`${year}C`] = [];
    res[`${year + 1}A`] = []; // A is Spring, C is Fall
  }
  return res;
}

interface SemestersProps {
  activeDegreeplan?: DegreePlan;
  showStats: any;
  className?: string;
  editMode: boolean;
  setModalKey: (arg0: ModalKey) => void;
  setModalObject: (obj: any) => void;
  setEditMode: (arg0: boolean) => void;
  isLoading: boolean;
  currentSemester?: string;
  ghosts?: GeneratedPlacement[];
  genBySemester?: Record<string, SemesterGenConfig>;
  onGenConfig?: (semester: string, next: SemesterGenConfig) => void;
  onSemesterKeys?: (keys: string[]) => void;
  syntheticKeys?: string[];
  onPinSlot?: (slotId: string, semester: string) => void;
  onUnpinSlot?: (slotId: string) => void;
  pinnedSlots?: Record<string, string>;
  /** Off hides summer boxes, except a summer that already holds courses. */
  showSummer?: boolean;
}

const Semesters = ({
  activeDegreeplan,
  showStats,
  className,
  editMode,
  setModalKey,
  setModalObject,
  setEditMode,
  currentSemester,
  isLoading,
  ghosts = [],
  genBySemester,
  onGenConfig,
  onSemesterKeys,
  syntheticKeys = [],
  onPinSlot,
  onUnpinSlot,
  pinnedSlots,
  showSummer = true,
}: SemestersProps) => {
  const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<
    Fulfillment[]
  >(
    activeDegreeplan
      ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments`
      : null
  );
  // semesters is state mostly derived from fulfillments

  const getDefaultSemesters = useCallback(() => {
    const startingYear = currentSemester ? Number(currentSemester.substring(0, 4)) : new Date().getFullYear(); // Use current semester as default starting semester
    return interpolateSemesters(startingYear, startingYear + 4);
  }, [currentSemester]);

  const [semesters, setSemesters] = useState<{
    [semester: string]: Fulfillment[];
  }>({});
  const addSemester = (semester: string) => {
    if (!semesters[semester]) setSemesters({ ...semesters, [semester]: [] });
  };

  const numUpdates = useRef<number>(-1);
  const currNumUpdates = useRef<number>(0);

  const removeSemester = (semester: string) => {
    numUpdates.current = semesters[semester].length

    if (semesters[semester]) {
      var newSems: { [semester: string]: Fulfillment[] } = {};
      for (var sem in semesters) {
        if (sem !== semester) newSems = { ...newSems, [sem]: semesters[sem] };
      }
      setSemesters(newSems);
    }
  };

  /** Get semesters from local storage */
  useEffect(() => {
    if (!activeDegreeplan) return;
    if (typeof window === "undefined") return setSemesters(getDefaultSemesters());
    const stickyValue = localStorage.getItem(
      getLocalSemestersKey(activeDegreeplan.id)
    );
    if (stickyValue === null) return setSemesters(getDefaultSemesters());
    let parsed;
    try {
      parsed = JSON.parse(stickyValue)
      setSemesters(parsed)
    } catch {
      setSemesters(getDefaultSemesters());
    }
  }, [activeDegreeplan, currentSemester]);

  // TODO: Bug where edit mode would always be set to true. When initializing, semesters updates multiple times,
  // so we can't be sure that we actually have no courses and should enter edit mode. 
  // I made a quick fix: it seems like semesters updates 5-6 times when initializing, so I just have it wait until
  // then to set edit mode to true if necessary. There is likely a better way to do this.
  const updateCounter = useRef(0);

  /** Update semesters to local storage */
  useEffect(() => {
    updateCounter.current = updateCounter.current + 1;

    if (Object.keys(semesters).length == 0 && !isLoading && updateCounter.current >= 5) {
      setEditMode(true);
    } 

    // if finish loading and no semesters, we go to edit mode for the user to add new semesters
    if (!activeDegreeplan) return;

    // && Object.keys(semesters).length
    if (typeof window !== "undefined" && Object.keys(semesters).length) {
      localStorage.setItem(
        getLocalSemestersKey(activeDegreeplan.id),
        JSON.stringify(semesters)
      );
    }
  }, [semesters, activeDegreeplan]);

  useEffect(() => {
    onSemesterKeys?.(Object.keys(semesters));
  }, [semesters]);

  const semesterKeyList = Object.keys(semesters).sort().join("|");
  useEffect(() => {
    const withGhosts = new Set(ghosts.map((ghost) => ghost.semester).filter(Boolean));
    setSemesters((current) => {
      const next = { ...current };
      let changed = false;
      syntheticKeys.forEach((key) => {
        if (withGhosts.has(key) && !next[key]) {
          next[key] = [];
          changed = true;
        }
      });
      // A trailing column with no courses and no suggestions is not part of the plan.
      Object.keys(next).forEach((key) => {
        if (!/^\d{4}[ABC]$/.test(key)) return;
        if ((next[key] || []).length > 0 || withGhosts.has(key)) return;
        if (key <= (currentSemester || "")) return;
        const laterHasWork = Object.keys(next).some(
          (other) =>
            /^\d{4}[ABC]$/.test(other) &&
            other > key &&
            ((next[other] || []).length > 0 || withGhosts.has(other))
        );
        if (laterHasWork) return;
        delete next[key];
        changed = true;
      });
      return changed ? next : current;
    });
  }, [syntheticKeys, ghosts, currentSemester, semesterKeyList]);

  /** Parse fulfillments and group them by semesters */
  useEffect(() => {
    if (!activeDegreeplan || !fulfillments || isLoadingFulfillments) return; // TODO: need more logic in this case
    currNumUpdates.current = currNumUpdates.current + 1;
    if (currNumUpdates.current >= numUpdates.current) {
      setSemesters((currentSemesters) => {
        const semesters = {} as { [semester: string]: Fulfillment[] };
        Object.keys(currentSemesters).forEach((semester) => {
          semesters[semester] = [];
        });
        fulfillments.forEach((fulfillment) => {
          if (!fulfillment.semester) return;
          if (!semesters[fulfillment.semester]) {
            semesters[fulfillment.semester] = [];
          }
          semesters[fulfillment.semester].push(fulfillment);
        });
        currNumUpdates.current = 0;
        numUpdates.current = -1;
        return semesters;
      });
    } 
  }, [fulfillments, activeDegreeplan, isLoadingFulfillments]);

  const visibleSemesters = Object.keys(semesters)
    .sort((a, b) => a.localeCompare(b))
    .filter((key, _index, all) => {
      if (!/^\d{4}[ABC]$/.test(key)) return true;
      const hasFulfillment = (semesters[key] || []).length > 0;
      const hasGhost = ghosts.some((ghost) => ghost.semester === key);
      if (hasFulfillment || hasGhost) return true;
      if (key <= (currentSemester || "")) return true;
      return all.some(
        (other) =>
          /^\d{4}[ABC]$/.test(other) &&
          other > key &&
          ((semesters[other] || []).length > 0 || ghosts.some((ghost) => ghost.semester === other))
      );
    });

  const [transferCollapsed, setTransferCollapsed] = useState(true);
  useEffect(() => {
    if (!activeDegreeplan || typeof window === "undefined") return;
    const stored = localStorage.getItem(transferCollapsedKey(activeDegreeplan.id));
    setTransferCollapsed(stored === null ? true : stored === "true");
  }, [activeDegreeplan?.id]);
  const toggleTransfer = () => {
    const next = !transferCollapsed;
    setTransferCollapsed(next);
    if (activeDegreeplan && typeof window !== "undefined") {
      localStorage.setItem(transferCollapsedKey(activeDegreeplan.id), String(next));
    }
  };

  const [collapsedYears, setCollapsedYears] = useState<number[]>([]);
  useEffect(() => {
    if (!activeDegreeplan || typeof window === "undefined") return;
    try {
      const stored = JSON.parse(localStorage.getItem(collapsedYearsKey(activeDegreeplan.id)) || "[]");
      setCollapsedYears(Array.isArray(stored) ? stored.filter(Number.isInteger) : []);
    } catch {
      setCollapsedYears([]);
    }
  }, [activeDegreeplan?.id]);
  const toggleYear = (academic: number) => {
    const next = collapsedYears.includes(academic)
      ? collapsedYears.filter((year) => year !== academic)
      : [...collapsedYears, academic];
    setCollapsedYears(next);
    if (activeDegreeplan && typeof window !== "undefined") {
      localStorage.setItem(collapsedYearsKey(activeDegreeplan.id), JSON.stringify(next));
    }
  };
  const yearCredits = (academic: number) =>
    SEASONS.reduce(
      (total, { code }) =>
        total +
        (semesters[termKey(academic, code)] || []).reduce(
          (sum, fulfillment) => sum + (Number(fulfillment.course?.credits) || 1),
          0
        ),
      0
    );

  const renderSemester = (semester: string, extra: Partial<React.ComponentProps<typeof FlexSemester>> = {}) => (
    <FlexSemester
      activeDegreeplanId={activeDegreeplan?.id}
      showStats={showStats}
      semester={semester}
      fulfillments={semesters[semester] || []}
      key={semester}
      editMode={editMode}
      removeSemester={removeSemester}
      setModalKey={setModalKey}
      setModalObject={setModalObject}
      currentSemester={currentSemester}
      numSemesters={Object.keys(semesters).length}
      ghosts={ghosts.filter((ghost) => ghost.semester === semester)}
      genConfig={genBySemester?.[semester]}
      onGenConfig={onGenConfig ? (next) => onGenConfig(semester, next) : undefined}
      onPinSlot={onPinSlot}
      onUnpinSlot={onUnpinSlot}
      pinnedSlots={pinnedSlots}
      {...extra}
    />
  );

  const visibleTerms = visibleSemesters.filter(isTermKey);
  const otherKeys = visibleSemesters.filter(
    (key) => !isTermKey(key) && key !== TRANSFER_CREDIT_SEMESTER_KEY
  );
  const academicYears = visibleTerms.map(academicYear);
  const firstYear = academicYears.length ? Math.min(...academicYears) : null;
  const lastYear = academicYears.length ? Math.max(...academicYears) : null;
  const years =
    firstYear === null || lastYear === null
      ? []
      : Array.from({ length: lastYear - firstYear + 1 }, (_, index) => firstYear + index);

  const baseColumns = showSummer ? 3 : 2;
  const seasonsFor = (academic: number) =>
    SEASONS.filter(
      ({ code }) =>
        code !== "B" || showSummer || (semesters[termKey(academic, code)] || []).length > 0
    );

  if (isLoading) {
    return (
      <SemestersContainer className={className}>
        <YearGrid $columns={baseColumns}>
          {Array.from(Array(6).keys()).map((index) => (
            <SkeletonSemester key={index} showStats={showStats} />
          ))}
        </YearGrid>
      </SemestersContainer>
    );
  }

  return (
    <SemestersContainer className={className}>
      {renderSemester(TRANSFER_CREDIT_SEMESTER_KEY, {
        editMode: false,
        collapsed: transferCollapsed,
        onToggleCollapsed: toggleTransfer,
      })}
      {years.map((academic, index) => {
        const collapsed = collapsedYears.includes(academic);
        return (
        <YearSection key={academic}>
          <YearLabel type="button" onClick={() => toggleYear(academic)} aria-expanded={!collapsed}>
            <i className={`fas fa-chevron-${collapsed ? "right" : "down"}`} />
            {yearName(index)} · {academic}–{String(academic + 1).slice(2)}
            {collapsed && <YearSummary>{yearCredits(academic).toFixed(1)} CU</YearSummary>}
          </YearLabel>
          {!collapsed && (
          <YearGrid $columns={seasonsFor(academic).length}>
            {seasonsFor(academic).map(({ code, label }) => {
              const key = termKey(academic, code);
              if (semesters[key] !== undefined) return renderSemester(key);
              return (
                <EmptyTerm key={key} type="button" onClick={() => addSemester(key)}>
                  <i className="fas fa-plus" />
                  {label} {key.slice(0, 4)}
                </EmptyTerm>
              );
            })}
          </YearGrid>
          )}
        </YearSection>
        );
      })}
      {otherKeys.map((key) => renderSemester(key))}
      {editMode && (
        <YearGrid $columns={baseColumns}>
          <ModifySemesters addSemester={addSemester} semesters={semesters} />
        </YearGrid>
      )}
    </SemestersContainer>
  );
};

export default Semesters;
