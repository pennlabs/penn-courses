
import Semester from "./Semester"
import styled from "@emotion/styled";
import { Icon } from "../bulma_derived_components";
import { Course, DegreePlan, Fulfillment } from "@/types";
import useSWR from "swr";
import { useEffect, useState } from "react";

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
    gap: 1rem;
    flex-wrap: wrap;
;`

const FlexSemester = styled(Semester)`
    flex: 1 1 15rem;
`;

const AddSemesterContainer = styled.div`
    flex: 1 1 15rem;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;
const AddSemester = styled.div`
    width: 100%;
    display: flex;
    justify-content: space-between;
    background-color: rgba(32, 156, 238, .9);
    padding: 1rem;
    border-radius: 10px;
    align-items: center;
    color: white;
`

const EditSemester = styled(AddSemester)`
    background-color: rgb(255, 193, 7);
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
            <AddSemester role="button" onClick={() => addSemester(getNextSemester(semesterKeys[semesterKeys.length - 1] || "2023C"))}>
                <Icon>
                    <i className="fas fa-plus"></i>
                </Icon>
                <div>
                    Add Semester
                </div>
            </AddSemester>
            <EditSemester role="button">
                <Icon>
                    <i className="fas fa-edit"></i>
                </Icon>
                <div>
                    Edit Semesters
                </div>
            </EditSemester>
        </AddSemesterContainer>
    )
}

interface SemestersProps {
    activeDegreeplan: DegreePlan | undefined;
    showStats: any;
    className: string
}

const Semesters = ({ activeDegreeplan, showStats, className }: SemestersProps) => {
    const { data: fulfillments, isLoading: isLoadingFulfillments } = useSWR<Fulfillment[]>(activeDegreeplan ? `/api/degree/degreeplans/${activeDegreeplan.id}/fulfillments` : null);    
    // semesters is state mostly derived from fulfillments
    const [semesters, setSemesters] = useState<{[semester: string]: Fulfillment[]}>({});
    const addSemester = (semester: string) => { if (!semesters[semester]) setSemesters({...semesters, [semester]: []}) };
    const defaultSemesters = {} as { [semester: string]: Fulfillment[] };
    useEffect(() => {
        if (!activeDegreeplan) return;
        if (typeof window === "undefined") return setSemesters(defaultSemesters); // default state
        const stickyValue = localStorage.getItem(getLocalSemestersKey(activeDegreeplan.id));
        setSemesters(
            stickyValue !== null
            ? JSON.parse(stickyValue)
            : defaultSemesters
        );
    }, [activeDegreeplan])

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

    useEffect(() => {
        if (!activeDegreeplan) return;
        if (typeof window !== undefined) {
            localStorage.setItem(getLocalSemestersKey(activeDegreeplan.id), JSON.stringify(semesters));
        }
    }, [semesters, activeDegreeplan])

    return (
        <SemestersContainer className={className}>            
            {Object.keys(semesters).sort().map((semester: any, index: number) =>
                <FlexSemester activeDegreeplanId={activeDegreeplan?.id} showStats={showStats} semester={semester} fulfillments={semesters[semester]} key={semester}/>
                )}
            <ModifySemesters addSemester={addSemester} semesters={semesters} />
        </SemestersContainer>
    )
}

export default Semesters;