
import Semester from "./Semester"
import styled from "@emotion/styled";
import { Icon } from "../bulma_derived_components";
import { DegreePlan, Fulfillment } from "@/types";
import useSWR from "swr";
import { useEffect, useState } from "react";
import assert from "assert";
import { mdiConsoleLine } from "@mdi/js";

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
    setEmptySemesters: (emptySemesters: string[]) => void;
    emptySemesters: string[];
    className: string;
}

const ModifySemesters = ({ setEmptySemesters, emptySemesters, className }: ModifySemestersProps) => {
    return (
        // TODO: add a modal for this
        <AddSemesterContainer className={className}>
            <AddSemester role="button" onClick={() => setEmptySemesters([...emptySemesters, getNextSemester(emptySemesters[emptySemesters.length-1] || "2023C")])}>
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
    
    // Empty semesters is expected to be kept in sorted order
    const [emptySemesters, setEmptySemesters] = useState<string[]>(["2021C", "2021C", "2022A", "2022C", "2023A", "2023C", "2024A", "2024C", "2025A"]);
    
    // semesters is state derived from fulfillments (we don't set it directly)
    const [semesters, setSemesters] = useState<{ [semester: string]: Fulfillment[] }>({});
    useMemo(() => {
        if (!fulfillments) return; // TODO: need more logic in this case
        assert(activeDegreeplan)
        const _semesters = fulfillments.reduce((semesters, fulfillment) => {
            if (!semesters[fulfillment.semester]) {
                semesters[fulfillment.semester] = [];
            }
            semesters[fulfillment.semester].push(fulfillment);
            return semesters;
        }, {} as { [semester: string]: Fulfillment[] });
        const _emptySemesters = emptySemesters.filter(semester => !_semesters[semester]?.length);
        Object.entries(semesters).forEach(([semester, values]) => { if (!values.length) _emptySemesters.push(semester) });
        _emptySemesters.forEach(semester => _semesters[semester] = []);
        _emptySemesters.sort()
        console.log("EMPTY SEMESTERS", _emptySemesters)
        setSemesters(_semesters);
        setEmptySemesters(_emptySemesters);
    }, [fulfillments, semesters, emptySemesters]);

    return (
        <SemestersContainer className={className}>            
            {Object.keys(semesters).sort().map((semester: any, index: number) =>
                <FlexSemester activeDegreeplanId={(activeDegreeplan as DegreePlan).id} showStats={showStats} semester={semester} fulfillments={semesters[semester]} key={semester}/>
                )}
            <ModifySemesters emptySemesters={emptySemesters} setEmptySemesters={setEmptySemesters}/>
        </SemestersContainer>
    )
}

export default Semesters;