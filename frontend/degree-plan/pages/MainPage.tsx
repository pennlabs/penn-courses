
// import { ToastContainer } from 'react-toastify'
import Nav from '../components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage';
import React, { useEffect, useState } from "react";
import { redirectForAuth, apiCheckAuth} from '../services/AuthServices';

const MainPage = () => {
    // const [authed, setAuthed] = useState(false);
    // const [authFailed, setAuthFailed] = useState(false);

    // useEffect(() => {
    //     apiCheckAuth()
    //     .then(isAuthed => {
    //         if (!isAuthed) {
    //         redirectForAuth();
    //         }
    //         setAuthed(isAuthed);
    //     })
    //     .catch(() => setAuthFailed(true));
    // }, []);

    // if (authFailed) {
    //     return (
    //         <div>
    //             Could not perform Platform authentication.
    //             <br />
    //             Refresh this page to try again.
    //         </div>
    //     );
    // }
    // if (authed)
        return (
            <>
                {/* <ToastContainer /> */}
                <Nav />
                <FourYearPlanPage />
            </>
        )
}

export default MainPage;

/**
 * A wrapper around a review page that performs Shibboleth authentication.
 */
