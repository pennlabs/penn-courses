
import FlexSemester, { SkeletonSemester } from "./Semester"
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import { Course, DegreePlan, Fulfillment } from "@/types";
import useSWR from "swr";
import React, { useEffect, useState } from "react";

const getNextSemester = (semester: string) => {
    console.log("GET NEXT SEMESTER")
    const year = parseInt(semester.slice(0, 4));
    const season = semester.slice(4);
    if (season === "A") {
        return `${year}C`;
    } else {
        return `${year+1}A`;
    }
}

const getLocalSemestersKey = (degreeplanId: DegreePlan["id"]) => `PDP-${degreeplanId}-semesters`;

const SemestersContainer = styled.div`
    display: flex;
    flex-direction: row;
    gap: 1.25rem;
    flex-wrap: wrap;
;`

// const AddSemesterContainer = styled.div`
//     flex: 1 1 15rem;
//     display: flex;
//     flex-direction: column;
//     gap: .5rem;
// `;

const AddSemesterContainer  = styled.div`
    background: #FFFFFF;
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
`

const PlusIcon = styled(Icon)`
    width: 100%;
    align-items: center;
`

const AddButton = styled.div`
    align-items: center;
    display: flex;
    flex-direction: column;
    gap: 1rem;
`

// TODO: get a consistent color palette across PCx
interface ModifySemestersProps {
    addSemester: (semester: Course["semester"]) => void;
    className: string;
    semesters: { [semester: string]: Fulfillment[] };
}

const ModifySemesters = ({ addSemester, semesters, className }: ModifySemestersProps) => {
    const semesterKeys = Object.keys(semesters).sort();
    return (
        // TODO: add a modal for this
        <AddSemesterContainer className={className}>
            <AddButtonContainer role="button" onClick={() => addSemester(getNextSemester(semesterKeys[semesterKeys.length - 1] || "2023C"))}>
                <AddButton >
                    <PlusIcon>
                        <i className="fas fa-plus fa-lg"></i>
                    </PlusIcon>
                    <div>
                        Add Semester
                    </div>
                </AddButton>
            </AddButtonContainer>
        </AddSemesterContainer>
    )
}

interface SemestersProps {
    activeDegreeplan: DegreePlan | undefined;
    showStats: any;
    className?: string;
    editMode: boolean;
    setModalKey: (arg0: string) => void;
    setModalObject: (obj: any) => void;
    setEditMode: (arg0: boolean) => void;
    isLoading: boolean;
    currentSemester: string;
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
    isLoading
}: SemestersProps) => {
    const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<Fulfillment[]>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments` : null);    
    // semesters is state mostly derived from fulfillments

    const getDefaultSemesters = React.useCallback(() => {
        if (!currentSemester) return {};

        var startingYear, graduationYear;
        if (typeof window === "undefined") {
            startingYear = Number(currentSemester.substring(0, 4)); // Use current semester as default starting semester
            graduationYear = startingYear + 4;
        } else {
            const startGradYearStr = localStorage.getItem('PDP-start-grad-years');
            if (!!startGradYearStr) {
                const startGradYear = JSON.parse(startGradYearStr);
                startingYear = startGradYear.startingYear;
                graduationYear = startGradYear.graduationYear;
            } else {
                return {}; 
            }
        }

        var res = {} as {[semester: string]: Fulfillment[]};
        for (var year = startingYear; year < graduationYear; year++) {
            res = {...res, [`${year}C`]: [], [`${year + 1}A`]: []}; // A is Spring, C is Fall
        }
        return res;
        
    }, [currentSemester]);

    const [semesters, setSemesters] = useState<{[semester: string]: Fulfillment[]}>({});
    const addSemester = (semester: string) => { if (!semesters[semester]) setSemesters({...semesters, [semester]: []}) };

    const removeSemester = (semester: string) => {
        if (semesters[semester]) {
            var newSems : {[semester: string]: Fulfillment[]} = {};
            for (var sem in semesters) {
                if (sem !== semester) newSems = {...newSems, [sem]: semesters[sem]};
            }
            setSemesters(newSems);
        }
    }

    const semesterCompare = (a, b) => {
        if (a.substring(0, 4) !== b.substring(0, 4)) return a - b; // compare year is years are different
        else return a.substring(4) - b.substring(4); // compare semester if years are the same
    }

    /** Get semesters from local storage */
    useEffect(() => {
        if (!activeDegreeplan) return;
        if (typeof window === "undefined") return setSemesters(getDefaultSemesters()); // default state
        const stickyValue = localStorage.getItem(getLocalSemestersKey(activeDegreeplan.id));
        setSemesters(
            stickyValue !== null
            ? JSON.parse(stickyValue)
            : getDefaultSemesters()
        );
    }, [activeDegreeplan])

    /** Update semesters to local storage */
    useEffect(() => {
        if (Object.keys(semesters).length == 0 && !isLoading) setEditMode(true); // if finish loading and no semesters, we go to edit mode for the user to add new semesters
        else setEditMode(false);
        if (!activeDegreeplan) return;
        if (typeof window !== undefined) {
            localStorage.setItem(getLocalSemestersKey(activeDegreeplan.id), JSON.stringify(semesters));
        }
    }, [semesters, activeDegreeplan])

    /** Parse fulfillments and group them by semesters */
    useEffect(() => {
        if (!activeDegreeplan || !fulfillments) return; // TODO: need more logic in this case
        setSemesters(currentSemesters => {
            const semesters = {} as { [semester: string]: Fulfillment[] };
            Object.keys(currentSemesters).forEach(semester => { semesters[semester] = [] });
            fulfillments.forEach(fulfillment => {
                if (!fulfillment.semester) return;
                if (!semesters[fulfillment.semester]) {
                    semesters[fulfillment.semester] = [];
                }
                semesters[fulfillment.semester].push(fulfillment);
            });
            return semesters
        })
    }, [fulfillments, activeDegreeplan]);

    return (
        <SemestersContainer className={className}>            
            {isLoading ? Array.from(Array(8).keys()).map(() => <SkeletonSemester showStats={showStats} />) :
            Object.keys(semesters).sort(semesterCompare).map((semester: any) =>
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
                    />
                )}
            {editMode && <ModifySemesters addSemester={addSemester} semesters={semesters} />}
        </SemestersContainer>
    )
}

export default Semesters;