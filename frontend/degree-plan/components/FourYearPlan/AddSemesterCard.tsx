import { useState } from "react";
import {semesterCardStyle} from './Semester';


const AddSemesterCard = ({semesters, setSemesters, showStats}) => {
    const [addMode, setAddMode] = useState(false);
    const [name, setName] = useState("");

    const handleAddSem = () => {
        setSemesters([...semesters, {id: semesters.length, name: name, cu: 0, courses:[]}]);
        setAddMode(false);
    }

    return (
        <div className="card" style={{...semesterCardStyle, minWidth: showStats? '250px' : '150px', maxWidth: showStats ? '400px' : '190px'}}>
            {addMode ?
                <div>
                    <div className="mt-1 ms-2 mb-1" style={{fontWeight:500}}>
                        Semester's name:
                    </div>
                    <input type='text' value={name} onChange={(e) => setName(e.target.value)}/>
                    <button onClick={handleAddSem}>submit</button>
                </div>
            :
            <button onClick={() => setAddMode(true)}>
                +
            </button>}
        </div>);
}

export default AddSemesterCard;