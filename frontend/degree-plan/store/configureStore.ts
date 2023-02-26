
import { configureStore } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/dist/query';
// import { coursesApi } from '../services/courseServices';
import reducer from './reducer';
import { createWrapper } from "next-redux-wrapper";

export const makeStore = () => configureStore(
    {
        reducer: reducer,
        // middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(coursesApi.middleware)
    });

setupListeners(makeStore().dispatch);

export type AppStore = ReturnType<typeof makeStore>;

export const wrapper = createWrapper<AppStore>(makeStore);

export interface ISemester {
    name: string,
    courses: ICourse[]
}

export interface ICourse {
    id: string,
    title: string,
    description: string,
    semester: string,
    num_sections: number,
    course_quality: number,
    instructor_quality: number,
    difficulty: number,
    work_required: number,
    recommendation_score: number,
    added: boolean,
    dept: string,
    number: string,
    note: string
}


export interface IEntities {
    semesters: ISemester[]
}

export interface RootState {
    entities: IEntities,
  }
const store = makeStore()
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch