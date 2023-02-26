import {combineReducers} from 'redux';
import entitiesReducer from './reducers/courses';
import { coursesApi } from '../services/courseServices';

export default combineReducers({
    // [coursesApi.reducerPath] : coursesApi.reducer,
    entities: entitiesReducer,
});