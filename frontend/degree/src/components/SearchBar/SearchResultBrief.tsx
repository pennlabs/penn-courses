import { useSelector } from 'react-redux';
import { RootState } from '../../store/configureStore';

const SearchResultBrief = () => {
    const loaded = useSelector((store : RootState) => store.search.loaded);
    const data = useSelector((store : RootState) => store.entities.courses);
    const queryString = useSelector((store : RootState) => store.search.queryString);
    const brief = !loaded ? 'Loading...' :`Showing ${data.length} results for ${queryString}`;

    return (
        <div className='d-flex justify-content-center'>
               <small>{brief}</small>
         </div>
    );
}

export default SearchResultBrief;