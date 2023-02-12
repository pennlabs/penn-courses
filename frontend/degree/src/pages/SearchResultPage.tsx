
import 'bootstrap/dist/css/bootstrap.css'
import 'react-toastify/dist/ReactToastify.css'
import '../App.css'
import SearchResultDetail from '../components/SearchResult/SearchResultDetail'
import { useSelector, useDispatch } from 'react-redux';
import { detailViewed, loadCourses } from '../store/reducers/courses';
import { loadedSet } from '../store/reducers/search';
import { RootState } from '../store/configureStore'
import { useGetCoursesQuery } from '../services/courseServices'

const SearchResultPage = () => {
    
    const dispatch = useDispatch();
    const showFilter = useSelector((store : RootState) => store.search.showFilter);
    const filterString = useSelector((store : RootState) => store.search.filterString);
    const filter = showFilter ? filterString : "";
    const query = useSelector((store : RootState) => store.search.queryString);

    // use RTK query to fetch data every time query or filter is changed
    const {data, isLoading, isFetching, isSuccess} = useGetCoursesQuery(query + filter);
    
    if (isSuccess) {
      dispatch(loadCourses(data));
      dispatch(loadedSet(true));
    } 
    if (isFetching) {
      dispatch(detailViewed(null)); // close detail window if a new search starts
      dispatch(loadedSet(false));
    }

  return (
    <>
      {!!isLoading && 
        <div className='d-flex justify-content-center'>
          <small>Loading...</small>
        </div>}
      {!!data && <SearchResultDetail/>}
    </>
  );
}

export default SearchResultPage;