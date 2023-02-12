import {combineReducers} from 'redux';
import entitiesReducer from './reducers/courses';
import searchReducer from './reducers/search';
import navReducer from './reducers/nav';
import { coursesApi } from '../services/courseServices';

export default combineReducers({
    [coursesApi.reducerPath] : coursesApi.reducer,
    search: searchReducer,
    entities: entitiesReducer,
    nav:navReducer
});