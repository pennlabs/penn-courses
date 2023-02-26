
// import { ToastContainer } from 'react-toastify'
import Nav from '../components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage';
import { useSelector } from 'react-redux';
import { RootState } from '../store/configureStore.js';

const MainPage = () => {

    return (
        <>
            {/* <ToastContainer /> */}
            <Nav />
            <FourYearPlanPage />
        </>
    )
}

export default MainPage;