import {noteAdded, noteTrashed} from '../../store/reducers/courses';
import { useDispatch, useSelector } from 'react-redux';
import { useEffect, useState } from "react";
import { toastSuccess, toastWarn } from '../../services/NotificationServices';
import { RootState } from '../../store/configureStore';

const Note = () => {
    const handleTrash = () => {
        dispatch(noteTrashed({course: course}));
        toastWarn('Note deleted!');
    }

    const handleNote = () => {
        if (!note) toastWarn('Note cannot be empty!');
        else {
            dispatch(noteAdded({course: course, note: note}));
            toastSuccess('Note saved!');
        }
    }
    
    const course = useSelector((store : RootState) => store.entities.current);
    const dispatch = useDispatch();

    const [note, setNote] = useState(course ? course.note : "");
    useEffect(() => {
        if (course) setNote(course.note);
    },[course]);

    return (
        <div className="d-flex justify-content-between">
            <div className="col-11 ms-1 me-1">
                <textarea name='note' className='form-control' placeholder='A sticky note for this course!' 
                        value={note} onChange={e => setNote(e.currentTarget.value)} rows={2}/>
            </div>
            <div>
                <button onClick={() => handleNote() } className="me-2 ms-1 btn btn-sm btn-outline-warning" > ✏️ </button>
                {course.note && // if note already written, give user the option to delete the note
                    <button onClick={() => handleTrash()} className="ms-1 mt-1 btn btn-sm btn-outline-warning" > 🗑 </button>}
            </div>
        </div>
    );
}

export default Note;