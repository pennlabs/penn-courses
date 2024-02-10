
import Semester from "./Semester"
import styled from "@emotion/styled";
import { Icon } from "../bulma_derived_components";

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

const ModifySemesters = ({ setSemesters, semesters, showStats, className }: any) => {
    return (
        <AddSemesterContainer className={className}>
            <AddSemester role="button">
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

const Semesters = ({semesters, addCourse, setSemesters, showStats, className }: any) => {
    return (
        <SemestersContainer className={className}>            
            {semesters.map((semester: any, index: number) => 
                <FlexSemester showStats={showStats} semester={semester} addCourse={addCourse} index={index}/>
                )}
            <ModifySemesters>
            </ModifySemesters>
        </SemestersContainer>
    )
}

export default Semesters;