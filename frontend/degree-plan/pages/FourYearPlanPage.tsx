import React, {useState, useEffect, useRef} from "react";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import SearchPanel from "../components/Search/SearchPanel";
// import Plan from "../components/example/Plan";
import axios from "../services/HttpServices"
import CourseDetailPanel from "@/components/Course/CourseDetailPanel";
import styled from "@emotion/styled";
import useSWR from "swr";
import { Course, DegreePlan, Options } from "@/types";
import ReviewPanel from "@/components/Infobox/ReviewPanel";
import { ReviewPanelContext } from '@/components/Infobox/ReviewPanel';
import DegreeModal, { ModalKey } from "@/components/FourYearPlan/DegreeModal";

const Row = styled.div`
    display: flex;
    flex-direction: row;
`;

const PlanPageContainer = styled.div`
    background-color: #F7F9FC;
    padding: 1rem;
`;

export const PanelTopBar = styled.div`
    padding-left: 15px;
    padding-top: 7px;
    padding-bottom: 5px;
    padding-right: 15px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    width: 100%;
`;

const PanelContainer = styled.div<{$width?: Number}>`
    border-radius: 10px;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    margin: 10px;
    height: 82vh;
    width: ${props => props.$width ? props.$width + "px" : ""};
    overflow: hidden; /* Hide scrollbars */
`;

const Divider = styled.div`
    width: 10px;
    height: 20vh;
    border-radius: 10px;
    background-color: #C5D2F6;
    margin-left: 3px;
    margin-right: 3px;
    margin-top: 30vh;
`;

const FourYearPlanPage = () => {
    // resizeable panels
    const [leftWidth, setLeftWidth] = useState(800);
    const [drag, setDrag] = useState(false);
    const [x, setX] = useState(0);

    const [degreeModalOpen, setDegreeModalOpen] = React.useState(false);

    // edit modals for degree and degree plan
    const [modalKey, setModalKey] = useState<ModalKey>(null);
    const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // stores the which degreeplan is being updated using the modal

    // active degree plan
    const [activeDegreeplanId, setActiveDegreeplanId] = useState<null | DegreePlan["id"]>(null);
    const { data: degreeplans, isLoading: isLoadingDegreeplans } = useSWR<DegreePlan[]>('/api/degree/degreeplans');
    const { data: activeDegreePlan, isLoading: isLoadingActiveDegreePlan } = useSWR(activeDegreeplanId ? `/api/degree/degreeplans/${activeDegreeplanId}` : null);
    useEffect(() => {
        // recompute the active degreeplan id on changes to the degreeplans
        if (!degreeplans?.length) setActiveDegreeplanId(null);
        else if (!activeDegreeplanId || !degreeplans.find(d => d.id === activeDegreeplanId)) {
            const mostRecentUpdated = degreeplans.reduce((a,b) => a.updated_at > b.updated_at ? a : b);
            setActiveDegreeplanId(mostRecentUpdated.id);
        }
    }, [degreeplans, activeDegreeplanId]);

    // review panel
    const { data: options } = useSWR<Options>('/api/options');
    const [reviewPanelCoords, setReviewPanelCoords] = useState<{x: number, y: number}>({ x: 0, y: 0 });
    const [reviewPanelFullCode, setReviewPanelFullCode] = useState<Course["full_code"]|null>(null);
    const [reviewPanelIsPermanent, setReviewPanelIsPermanent] = useState(false);
    
    const [searchClosed, setSearchClosed] = useState(true);

    const [results, setResults] = useState([]);
    const [courseDetailOpen, setCourseDetailOpen] = useState(false);
    const [courseDetail, setCourseDetail] = useState({});


    const [highlightReqId, setHighlightReqId] = useState(-1);

    const handleCloseSearchPanel = () => {
        setHighlightReqId(-1);
        setSearchClosed(true);
    }

    // testing version
    const [majors, setMajors] = useState([{id: 1843, name: 'Computer Science, BSE'}, {id: 1744, name: 'Visual Studies, BAS'}]);
    const [currentMajor, setCurrentMajor] = useState({});
    useEffect(() => {
        if (majors.length !== 0) setCurrentMajor(majors[0]);
      }, [majors]);

    const ref = useRef(null);
    const [totalWidth, setTotalWidth] = useState(0);

    useEffect(() => {
        console.log("total width: ", ref.current ? ref.current.offsetWidth : 0);
        setTotalWidth(ref.current ? ref.current.offsetWidth : 0)
    }, [ref.current]);

    const pauseEvent = (e: any) => {
        if(e.stopPropagation) e.stopPropagation();
        if(e.preventDefault) e.preventDefault();
        e.cancelBubble=true;
        e.returnValue=false;
        return false;
    }

    const startResize = (e:any) => {
        setDrag(true);
        setX(e.clientX);
        pauseEvent(e)
    }

    const resizeFrame = (e:any) => {
        const criticalRatio = 0.3;
        if (drag) {
            const xDiff = Math.abs(x - e.clientX) * 1.1;
            let newLeftW = x > e.clientX ? leftWidth - xDiff : leftWidth + xDiff;            
            if (totalWidth - newLeftW < totalWidth * criticalRatio) newLeftW = totalWidth * (1 - criticalRatio);
            if (newLeftW < totalWidth * criticalRatio) newLeftW = totalWidth * criticalRatio;
            setX(e.clientX);
            setLeftWidth(newLeftW);
        }
    };

    const endResize = (e:any) => {
        setDrag(false);
        setX(e.clientX);
    }

    const [loading, setLoading] = useState(false);
    const handleSearch =  async (id: number) => {
        setHighlightReqId(id);
        setLoading(true);
        axios.get(`/degree/courses/${id}`).then(res => {
            let newData = [...res.data];
            setResults(newData);
            setLoading(false);
        });
    }

    const showCourseDetail = (course: any) => {
        setCourseDetailOpen(true);
        setCourseDetail(course);
    }
    
    return (
        <PlanPageContainer ref={ref}>
            <ReviewPanelContext.Provider value={{ 
            full_code: reviewPanelFullCode, 
            set_full_code: setReviewPanelFullCode, 
            isPermanent: reviewPanelIsPermanent, 
            setIsPermanent: setReviewPanelIsPermanent,
            position: reviewPanelCoords,
            setPosition: setReviewPanelCoords
            }}>
                {reviewPanelFullCode && 
                    <ReviewPanel 
                    currentSemester={options?.SEMESTER}
                    full_code={reviewPanelFullCode} 
                    set_full_code={setReviewPanelFullCode}
                    isPermanent={reviewPanelIsPermanent}
                    setIsPermanent={setReviewPanelIsPermanent}
                    position={reviewPanelCoords}
                    setPosition={setReviewPanelCoords}
                    />}
                {modalKey && 
                    <DegreeModal 
                    setModalKey={setModalKey} 
                    modalKey={modalKey} 
                    modalObject={modalObject} 
                    setActiveDegreeplanId={setActiveDegreeplanId}
                    /> 
                    }
                <Row onMouseMove={resizeFrame} onMouseUp={endResize}>
                    <PanelContainer $width={leftWidth}>
                        <PlanPanel 
                        setModalKey={setModalKey}
                        modalKey={modalKey}
                        setModalObject={setModalObject}
                        isLoading={isLoadingDegreeplans || isLoadingActiveDegreePlan} 
                        activeDegreeplan={activeDegreePlan} degreeplans={degreeplans} 
                        setActiveDegreeplanId={setActiveDegreeplanId}
                        />
                    </PanelContainer>
                    <Divider onMouseDown={startResize}/>
                    <PanelContainer $width={totalWidth - leftWidth}>
                        <ReqPanel 
                        setModalKey={setModalKey}
                        setModalObject={setModalObject}
                        activeDegreeplan={activeDegreePlan} 
                        highlightReqId={highlightReqId} 
                        setHighlightReqId={setHighlightReqId} 
                        setMajors={setMajors} 
                        currentMajor={currentMajor} 
                        setCurrentMajor={setCurrentMajor} 
                        setSearchClosed={setSearchClosed} 
                        setDegreeModalOpen={setDegreeModalOpen} 
                        handleSearch={handleSearch}
                        />
                    </PanelContainer>
                    <PanelContainer hidden={searchClosed}>
                        <SearchPanel setClosed={handleCloseSearchPanel} courses={results} showCourseDetail={showCourseDetail} loading={loading} searchReqId={highlightReqId}/>
                    </PanelContainer>
                </Row>
            </ReviewPanelContext.Provider>
        </PlanPageContainer>
    )
}

export default FourYearPlanPage;