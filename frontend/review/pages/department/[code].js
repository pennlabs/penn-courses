import React, { useRef, useEffect, useState } from "react";
// TODO move cookies to something else?
import { useRouter } from 'next/router'

import InfoBox from "../../components/InfoBox";
import ScoreBox from "../../components/ScoreBox";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import { apiReviewData, apiCheckAuth, redirectForAuth } from "../../utils/api";

const SHOW_RECRUITMENT_BANNER = false;

const DepartmentPage = ({
    code
}) => {
    // TODO: Abstract shared code between Dept, Course and Instruct into hooks

    const router = useRouter();
    const [data, setData] = useState({});
    const [rowCode, setRowCode] = useState(null);
    const [liveData, setLiveData] = useState(null);
    const [selectedCourses, setSelectedCourses] = useState({});
    const [isAverage, setIsAverage] = useState(false);

    const navigateToPage = value => value && router.push(value);
    const toggleIsAverage = () => {
        setIsAverage(!isAverage)
        localStorage.setItem("meta-column-type", isAverage ? "average" : "recent")
    }
    const getReviewData = async () => {
        const isAuthed = await apiCheckAuth();
        if (!isAuthed) redirectForAuth();
        const data = await apiReviewData('department', code)
        console.log(data)
        const { error, detail, name } = data;
        if (error) {
            // TODO: nextjs error handling
            return
        }
        setData(data);
    }

    // TODO: Move this code into instructor and course hooks
    // // Handle scrolling to new table
    // const scrollToRow = nextCode => {
    //     if (rowCode === nextCode) {
    //         setRowCode(null);
    //         return;
    //     }
    //     setRowCode(nextCode);
    // }
    // useEffect(() => {
    //     nextCode && window && window.scrollTo({
    //         behavior: "smooth",
    //         top: tableRef.current.offsetTop
    //     })
    // }, [nextCode])

    // Put in useEffect so it runs in the browser
    useEffect(() => {
        getReviewData();
        setIsAverage(localStorage.getItem("meta-column-type" !== "recent"))
    }, []);

    return (
        <div>
            <Navbar />
            {data ? (
                <div id="content" className="row">
                    <div className="col-sm-12 col-md-4 sidebar-col box-wrapper">
                        <InfoBox
                            type="department"
                            code={code}
                            data={data}
                            liveData={liveData}
                            selectedCourses={selectedCourses}
                        />
                    </div>
                    <div className="col-sm-12 col-md-8 main-col">
                        <ScoreBox
                            data={data}
                            type="department"
                            liveData={liveData}
                            onSelect={setSelectedCourses}
                            isAverage={isAverage}
                            setIsAverage={setIsAverage}
                        />
                    </div>
                </div>
            ) : (
                    <div style={{ textAlign: "center", padding: 45 }}>
                        <i
                            className="fa fa-spin fa-cog fa-fw"
                            style={{ fontSize: "150px", color: "#aaa" }}
                        />
                        <h1 style={{ fontSize: "2em", marginTop: 15 }}>
                            Loading {code}
          ...
        </h1>
                    </div>
                )}
            <Footer />
        </div>
    );
}

export const getServerSideProps = async ({
    params: {
        code
    }
}) => {
    return {
        props: {
            code
        }
    }
}

export default DepartmentPage;