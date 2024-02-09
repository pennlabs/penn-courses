
import Nav from '../components/NavBar/Nav'
import FourYearPlanPage from './FourYearPlanPage';
import React, { useEffect, useState } from "react";
import { redirectForAuth, apiCheckAuth} from '../services/AuthServices';

const MainPage = () => {
        return (
            <>
                <Nav />
                <FourYearPlanPage />
            </>
        )
}

export default MainPage;

/**
 * A wrapper around a review page that performs Shibboleth authentication.
 */
