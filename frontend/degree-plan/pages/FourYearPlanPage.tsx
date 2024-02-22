import React, {useState, useEffect, useRef} from "react";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import {SearchPanel, SearchPanelContext} from "../components/Search/SearchPanel";
// import Plan from "../components/example/Plan";
import CourseDetailPanel from "@/components/Course/CourseDetailPanel";
import styled from "@emotion/styled";
import useSWR from "swr";
import { Course, DegreePlan, Options, Rule } from "@/types";
import ReviewPanel from "@/components/Infobox/ReviewPanel";
import { ReviewPanelContext } from '@/components/Infobox/ReviewPanel';
import DegreeModal, { ModalKey } from "@/components/FourYearPlan/DegreeModal";
import SplitPane, { Pane } from 'react-split-pane';
import Dock from "@/components/Dock/Dock";
import Nav from "@/components/NavBar/Nav";

const Row = styled.div`
    position: relative;
    height: 100%;
    width: 100%;
`;

const PlanPageContainer = styled.div`
    background-color: var(--background-grey);
    padding: 0rem .5rem;
    position: absolute;
    width: 100%;
    height: 92%; /* TODO: this is hacky*/
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

const PanelContainer = styled.div<{$maxWidth: string, $minWidth: string}>`
    border-radius: 10px;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    margin: 9px;
    height: 82vh;
    overflow: hidden; /* Hide scrollbars */
    width: ${props => props.$maxWidth || props.$maxWidth ? 'auto' : '100%'};
    max-width: ${props => props.$maxWidth ? props.$maxWidth : 'auto'};
    min-width: ${props => props.$minWidth ? props.$minWidth : 'auto'};
    position: relative;
`;

const FourYearPlanPage = ({searchClosed, updateUser, user}: any) => {
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
    const [reviewPanelCoords, setReviewPanelCoords] = useState<{ top?: number, left?:number, right?: number, bottom?: number }>({ top: 0, left: 0 });
    const [reviewPanelFullCode, setReviewPanelFullCode] = useState<Course["full_code"]|null>(null);
    const ref = useRef(null);

    // search panel
    const [searchPanelOpen, setSearchPanelOpen] = useState<boolean>(false)
    const [searchRuleId, setSearchRuleId] = useState<Rule["id"] | null>(null);
    const [searchRuleQuery, setSearchRuleQuery] = useState<string | null>(null) // a query object

    
    return (

        <SearchPanelContext.Provider value={{
            setSearchPanelOpen: setSearchPanelOpen,
            searchPanelOpen: searchPanelOpen,
            setSearchRuleId: setSearchRuleId,
            searchRuleId: searchRuleId,
            setSearchRuleQuery: setSearchRuleQuery,
            searchRuleQuery: searchRuleQuery
        }}>
            <Nav
            login={updateUser}
            logout={() => updateUser(null)}
            user={user}
            />
            <PlanPageContainer ref={ref}>
                    <ReviewPanelContext.Provider value={{ 
                    full_code: reviewPanelFullCode, 
                    set_full_code: setReviewPanelFullCode, 
                    position: reviewPanelCoords,
                    setPosition: setReviewPanelCoords
                    }}>
                        {reviewPanelFullCode && 
                            <ReviewPanel 
                            currentSemester={options?.SEMESTER}
                            full_code={reviewPanelFullCode} 
                            set_full_code={setReviewPanelFullCode}
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
                        <Row>
                            <SplitPane split="vertical" minSize={0} maxSize={750} defaultSize='50%'>
                                <Pane>
                                    <PanelContainer>
                                        <PlanPanel 
                                            setModalKey={setModalKey}
                                            modalKey={modalKey}
                                            setModalObject={setModalObject}
                                            isLoading={isLoadingDegreeplans || isLoadingActiveDegreePlan} 
                                            activeDegreeplan={activeDegreePlan} degreeplans={degreeplans} 
                                            setActiveDegreeplanId={setActiveDegreeplanId}
                                        />
                                    </PanelContainer>
                                </Pane>
                                <Pane style={{display: 'flex', flexDirection: 'row'}}>
                                    <PanelContainer>
                                        {/* <SplitPane split="horizontal" minSize='80%'> */}
                                            <ReqPanel
                                                setModalKey={setModalKey}
                                                setModalObject={setModalObject}
                                                activeDegreeplan={activeDegreePlan} 
                                            />
                                            {/* <div>
                                                load area
                                            </div>
                                        </SplitPane> */}
                                    </PanelContainer>
                                    <PanelContainer hidden={!searchPanelOpen} $minWidth={'40%'} $maxWidth={'45%'} >
                                        <SearchPanel />
                                    </PanelContainer>
                                </Pane>
                            </SplitPane>
                                
                        </Row>             
                    </ReviewPanelContext.Provider>
            </PlanPageContainer>
        </SearchPanelContext.Provider>
    )
}

export default FourYearPlanPage;