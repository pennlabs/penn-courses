import FlexSemester, { SkeletonSemester } from "./Semester";
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import { Course, DegreePlan, Fulfillment } from "@/types";
import useSWR from "swr";
import React, { useEffect, useState } from "react";
import Select from "react-select";
import { ModalKey } from "./DegreeModal";

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

const SemestersContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 1.25rem;
  flex-wrap: wrap;
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
  font-size: 1rem;
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
    Object.keys(semesters).sort((a, b) => a.localeCompare(b)).pop() || "2026A"; // TODO: Change fallback value to start semester (based on onboarding?)

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
}: SemestersProps) => {
  const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<
    Fulfillment[]
  >(
    activeDegreeplan
      ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments`
      : null
  );
  // semesters is state mostly derived from fulfillments


  const getDefaultSemesters = React.useCallback(() => {
    const startingYear = currentSemester ? Number(currentSemester.substring(0, 4)) : new Date().getFullYear(); // Use current semester as default starting semester
    return interpolateSemesters(startingYear, startingYear + 4);
  }, [currentSemester]);

  const [semesters, setSemesters] = useState<{
    [semester: string]: Fulfillment[];
  }>({});
  const addSemester = (semester: string) => {
    if (!semesters[semester]) setSemesters({ ...semesters, [semester]: [] });
  };

  const removeSemester = (semester: string) => {
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

  /** Update semesters to local storage */
  useEffect(() => {
    if (Object.keys(semesters).length == 0 && !isLoading) setEditMode(true);
    // if finish loading and no semesters, we go to edit mode for the user to add new semesters
    if (!activeDegreeplan) return;
    if (typeof window !== "undefined" && Object.keys(semesters).length) {
      localStorage.setItem(
        getLocalSemestersKey(activeDegreeplan.id),
        JSON.stringify(semesters)
      );
    }
  }, [semesters, activeDegreeplan]);

  /** Parse fulfillments and group them by semesters */
  useEffect(() => {
    if (!activeDegreeplan || !fulfillments || isLoadingFulfillments) return; // TODO: need more logic in this case
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
      return semesters;
    });
  }, [fulfillments, activeDegreeplan, isLoadingFulfillments]);

  return (
    <SemestersContainer className={className}>
      {isLoading
        ? Array.from(Array(8).keys()).map(() => (
            <SkeletonSemester showStats={showStats} />
          ))
        : Object.keys(semesters)
            .sort((a,b) => a.localeCompare(b))
            .map((semester: any) => (
              <FlexSemester
                activeDegreeplanId={activeDegreeplan?.id}
                showStats={showStats}
                semester={semester}
                fulfillments={semesters[semester]}
                key={semester}
                editMode={editMode}
                removeSemester={removeSemester}
                setModalKey={setModalKey}
                setModalObject={setModalObject}
                currentSemester={currentSemester}
              />
            ))}
      {editMode && (
        <ModifySemesters addSemester={addSemester} semesters={semesters} />
      )}
    </SemestersContainer>
  );
};

export default Semesters;
