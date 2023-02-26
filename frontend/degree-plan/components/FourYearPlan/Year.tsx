import Semester from "./Semester";
import { yearName } from "../../styles/FourYearStyles";
import { IYear, ISemester } from "../../store/configureStore";

interface YearProps {
    year: IYear
}

const Year = ({year} : YearProps) => {
    return (
        <div className="me-3">
            <div className="mb-1" style={yearName}>
            {year.name}
            </div>
            {year.semesters.map( (semester : ISemester) => 
                <Semester year={year.name} semester={semester}/>
            )}
        </div>
    )
}

export default Year;