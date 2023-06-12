
import {createSlice} from '@reduxjs/toolkit';
import { ICourse, ISemester } from '../configureStore';
import semesters from '../../data/semesters';

const initialCourse = {
    id: "",
    title: "",
    description: "",
    semester: "",
    num_sections: "",
    course_quality: "",
    instructor_quality: "",
    difficulty: "",
    work_required: "",
    recommendation_score: "",
    added: false,
    dept: "",
    number: "",
    note: ""
};

const initialEntities = {
    semesters: semesters // [] as ISemester[]
}

/* For the structure of store.entities, please refer to configureStore file, 
    which lays out the structure of the store */
const slice = createSlice({
    name: 'entities',
    initialState: initialEntities,
    reducers: {
        addCourseToSem: (entities, action) => {
            // console.log(JSON.stringify(entities.semesters));
            // console.log(JSON.stringify(action.payload));
            const {dept, number} = action.payload.course;
            const [semester] = entities.semesters.filter(semester => semester.name === action.payload.semester);
            // console.log(JSON.stringify(semester));
            const [courseExists] = semester.courses.filter(c => c.dept === dept && c.number == number); // course already exists
            if (courseExists) return;
            else semester.courses.push(action.payload.course);
        },
        removeCourseFromSem: (entities, action) => {
            const {dept, number} = action.payload.course;
            const [semester] = entities.semesters.filter(semester => semester.name === action.payload.semester);
            // console.log(JSON.stringify(semester));
            semester.courses = semester.courses.filter(c => c.dept === dept && c.number == number);
        }
    }
})

export const {
    addCourseToSem, 
    removeCourseFromSem} = slice.actions;
export default slice.reducer;
