
import { ToastContainer } from 'react-toastify'
import Nav from '../components/Nav'
import SearchBar from '../components/SearchBar/SearchBar';
import SearchResultPage from './SearchResultPage';
import FourYearPlanPage from './FourYearPlanPage';
import { useSelector } from 'react-redux';
import { RootState } from '../store/configureStore.js';

const MainPage = () => {
    // some state control variables
    const onContentPage = useSelector((store : RootState) => store.nav.onContentPage);
    const showFourYearPlan = useSelector((store : RootState) => store.nav.showFourYearPlan);
    const hideSearchBar = useSelector((store : RootState) => store.nav.hideSearchBar);
    const query = useSelector((store : RootState) => store.search.queryString);

    return (
        <>
            <ToastContainer />
            <Nav />
            {!hideSearchBar && <SearchBar />}
            {showFourYearPlan && <FourYearPlanPage />}
            {!showFourYearPlan && onContentPage && query && <SearchResultPage/>}
        </>
    )
}

export default MainPage;