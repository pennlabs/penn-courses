
import {createSlice} from '@reduxjs/toolkit';
import { ICourse, ISemester } from '../configureStore';

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

const initialNote = {
    id: "",
    note: ""
}

const initialCart = {
    name: "Default", 
    courses: [] as ICourse[]
}

const initialEntities = {
    cart : initialCart,
    carts : [initialCart],
    notes : [initialNote],
    courses: [initialCourse],
    current: initialCourse,
    fourYears : [
            {
                name: '1st Year',
                semesters: 
                [
                    {
                        name: 'Fall',
                        courses:[] as ICourse[]
                    },
                    {
                        name: 'Spring',
                        courses:[] as ICourse[]
                    }
                ] as ISemester[]
            },
            {
                name: '2nd Year',
                semesters: 
                [
                    {
                        name: 'Fall',
                        courses:[] as ICourse[]
                    },
                    {
                        name: 'Spring',
                        courses:[] as ICourse[]
                    }
                ] as ISemester[]
            },
            {
                name: '3rd Year',
                semesters: 
                [
                    {
                        name: 'Fall',
                        courses:[] as ICourse[]
                    },
                    {
                        name: 'Spring',
                        courses:[] as ICourse[]
                    }
                ] as ISemester[]
            },
            {
                name: '4th Year',
                semesters: 
                [
                    {
                        name: 'Fall',
                        courses:[] as ICourse[]
                    },
                    {
                        name: 'Spring',
                        courses:[] as ICourse[]
                    }
                ] as ISemester[]
            }
        ]
}

/* For the structure of store.entities, please refer to configureStore file, 
    which lays out the structure of the store */
const slice = createSlice({
    name: 'entities',
    initialState: initialEntities,
    reducers: {
        // initialize courses, cart, fourYears, carts, notes, and showCart
        loadCourses: (entities, action) => {
            // if current course is in cart we need to update its status
            if (entities.current) {
                const [currentCourse] = entities.cart.courses.filter(c => c.id === entities.current.id);
                entities.current.added = !!currentCourse;
            }

            let courses = [...action.payload];
            courses = courses.map(c => ({...c}));
            courses = courses.filter(c => c.title && c.course_quality) // only keep courses with title

            for (let i = 0; i < courses.length; i++) {
                const [dept, number] = courses[i].id.split('-');
                courses[i].dept = dept;
                courses[i].number = number;

                // initialize added and note variables
                courses[i].added = false;
                courses[i].note = "";

                // note
                const [courseNoted] = entities.notes.filter(c => c.id === courses[i].id);
                if (courseNoted) courses[i].note = courseNoted.note;

                // update added courses from entities.cart
                const [courseInCart] = entities.cart.courses.filter(c => c.id === courses[i].id);
                if (courseInCart) courses[i].added = true;
            }
            courses = courses.sort((a, b) => a.number - b.number); // sort by course number
            entities.courses = courses;
        },
        detailViewed: (entities, action) => {
            if (!action.payload) {
                entities.current = initialCourse;
            } else {
                entities.current = action.payload;
            }
        },
        noteAdded: (entities, action) => {
            const course = action.payload.course;
            const id = course.id;
            const note = action.payload.note;
            const courses = [...entities.courses];
            const [target] = courses.filter(course => course.id === id);
            target.note = note;

            entities.notes.push({
                id: id,
                note: note
            })

            //update current course
            entities.current.note = note;

            // update carts
            for (let i = 0; i < entities.carts.length; i++) {
                const cart = entities.carts[i];
                const [courseNoted] = cart.courses.filter(c => c.id === course.id);
                if (courseNoted) courseNoted.note = note;
            }

            // update current cart
            const [courseNoted] = entities.cart.courses.filter(c => c.id === course.id);
            if (courseNoted) courseNoted.note = note;
        },
        noteTrashed: (entities, action) => {
            const course = action.payload.course;
            const id = action.payload.course.id;
            const courses = [...entities.courses];
            const [target] = courses.filter(course => course.id === id);
            target.note = "";

            //update current course
            entities.current.note = "";

            // update carts
            for (let i = 0; i < entities.carts.length; i++) {
                const cart = entities.carts[i];
                const [courseNoted] = cart.courses.filter(c => c.id === course.id);
                if (courseNoted) courseNoted.note = "";
            }

            // update current cart
            const [courseNoted] = entities.cart.courses.filter(c => c.id === course.id);
            if (courseNoted) courseNoted.note = "";
        },
        courseAdded: (entities, action) => {
            const courseToBeAdded = {...action.payload};
            // add course to cart
            courseToBeAdded.added = true;
            entities.cart.courses.push(courseToBeAdded); 

            // update course in carts
            const [currentCart] = entities.carts.filter(c => c.name === entities.cart.name);
            currentCart.courses.push(courseToBeAdded)

            // update course in entities.courses
            const [target] = entities.courses.filter(c => c.id === courseToBeAdded.id);
            if (target) target.added = true;

            //update course in entities.current
            if (entities.current) entities.current.added = true;
        },
        courseRemoved: (entities, action) => {
            const courseToBeRemoved = {...action.payload};
            entities.cart.courses = entities.cart.courses.filter(c => c.id !== courseToBeRemoved.id);

            // update course in carts
            const [cartRemovedFrom] = entities.carts.filter(c => c.name === entities.cart.name);
            cartRemovedFrom.courses = cartRemovedFrom.courses.filter(c => c.id !== courseToBeRemoved.id);

            // update course in entities.courses
            const [target] = entities.courses.filter(c => c.id === courseToBeRemoved.id);
            if (target) target.added = false;

            //update course in entities.current
            if (entities.current && entities.current.id === courseToBeRemoved.id) {
                entities.current.added = false;
            }
        },
        newCartCreated: (entities, action) => {
            console.log('wawa');
            const newCart = {name: action.payload, courses:[]};
            entities.carts.push(newCart);
            entities.cart = newCart;
            console.log(JSON.stringify(entities.current));
        },
        currentCartSet: (entities, action) => {
            entities.cart = action.payload;
        },
        cartSet: (entities, action) => {
            const [cartReordered] = entities.carts.filter(c => c.name == action.payload.name);
            cartReordered.courses = action.payload.courses;
            entities.cart = cartReordered;
        },
        courseAddedToSemester: (entities, action) => {
            const [year] = entities.fourYears.filter(year => year.name === action.payload.year);
            // console.log(JSON.stringify(year));
            const [semester] = year.semesters.filter(semester => semester.name === action.payload.semester);
            // console.log(JSON.stringify(semester));
            const [courseExists] = semester.courses.filter(c => c.id === action.payload.course.id); // course already exists
            if (courseExists) return;
            else semester.courses.push(action.payload.course);
        },
        courseRemovedFromSemester: (entities, action) => {
            const [year] = entities.fourYears.filter(year => year.name === action.payload.year);
            // console.log(JSON.stringify(year));
            const [semester] = year.semesters.filter(semester => semester.name === action.payload.semester);
            // console.log(JSON.stringify(semester));
            semester.courses = semester.courses.filter(c => c.id !== action.payload.course.id);
        }
    }
})

export const {
    loadCourses, 
    noteAdded, 
    noteTrashed, 
    detailViewed, 
    courseAdded, 
    courseRemoved, 
    newCartCreated, 
    currentCartSet, 
    cartSet,
    courseAddedToSemester, 
    courseRemovedFromSemester} = slice.actions;
export default slice.reducer;
