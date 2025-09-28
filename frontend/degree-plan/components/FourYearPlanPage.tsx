import React, { useState, useEffect, useRef, MutableRefObject } from "react";
import ReqPanel from "./Requirements/ReqPanel";
import PlanPanel from "./FourYearPlan/PlanPanel";
import {
    SearchPanel,
    SearchPanelContext,
} from "./Search/SearchPanel";
import styled from "@emotion/styled";
import useSWR from "swr";
import { Course, DegreePlan, Fulfillment, Options, Rule, User } from "@/types";
import ReviewPanel, { ReviewPanelContext } from "@/components/Infobox/ReviewPanel";
import TutorialModal, { TutorialModalKey, TutorialModalContext } from "./FourYearPlan/OnboardingTutorial";
import DegreeModal, { ModalKey } from "@/components/FourYearPlan/DegreeModal";
import SplitPane, { Pane } from "react-split-pane";
import Dock from "@/components/Dock/Dock";
import useWindowDimensions from "@/hooks/window";
import OnboardingPage from "./FourYearPlan/OnboardingPage";
import Footer from "./Footer";
import { SemestersContext } from "./FourYearPlan/Semesters";
import { getCsrf } from "@/hooks/swrcrud";

import ExpandedCoursesPanel from "./FourYearPlan/ExpandedCoursesPanel";
import { ExpandedCoursesPanelContext } from "./FourYearPlan/ExpandedCoursesPanel";

const PageContainer = styled.div`
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
`;

const Row = styled.div`
  position: relative;
  height: 100%;
  width: 100%;
`;

const BodyContainer = styled.div`
  background-color: var(--background-light-grey);
  width: 100%;
  flex-grow: 1;
`;

const PanelWrapper = styled(Pane)`
  padding: 5px;
  height: 100%;
  display: flex;
  flex-direction: row;
  gap: 1rem;
`

const PanelInteriorWrapper = styled.div<{ $maxWidth?: string; $minWidth?: string }>`
  border-radius: 10px;
  box-shadow: 0px 0px 5px 1px #00000026;
  overflow: hidden; /* Hide scrollbars */
  width: ${(props) => (props.$maxWidth || "100%")};
  max-width: ${(props) => (props.$maxWidth ? props.$maxWidth : "auto")};
  min-width: ${(props) => (props.$minWidth ? props.$minWidth : "auto")};
  position: relative;
  height: 100%;
`;


const FourYearPlanPage = ({
    updateUser,
    user,
    showTutorialModal,
}: any) => {
    // tutorial
    const [tutorialModalKey, setTutorialModalKey] = useState<TutorialModalKey>("welcome");
    const highlightedComponentRef = useRef<HTMLElement | null>(null);
    const componentRefs = useRef<Record<string, HTMLElement | null>>({});

    // edit modals for degree and degree plan
    const [modalKey, setModalKey] = useState<ModalKey>(null);
    const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // stores the which degreeplan is being updated using the modal
    const [showOnboardingModal, setShowOnboardingModal] = useState(false);
    const [activeDegreeplan, setActiveDegreeplan] = React.useState<DegreePlan | null>(null);

    const { data: degreeplans, isLoading: isLoadingDegreeplans } = useSWR<
        DegreePlan[]
    >("/api/degree/degreeplans");

    useEffect(() => {
        // recompute the active degreeplan id on changes to the degreeplans
        if (!isLoadingDegreeplans && !degreeplans?.length) {
            setShowOnboardingModal(true);
        }
        if (!degreeplans?.length) {
            setActiveDegreeplan(null);
        } else if (
            !activeDegreeplan || !degreeplans.find((d) => d.id === activeDegreeplan.id)
        ) {
            const mostRecentUpdated = degreeplans.reduce((a, b) =>
                a.updated_at > b.updated_at ? a : b
            );
            setActiveDegreeplan(mostRecentUpdated);
        }
    }, [degreeplans, isLoadingDegreeplans]);

    const windowWidth = useWindowDimensions()["width"];

    // review panel
    const { data: options } = useSWR<Options>("/api/options");

    const [reviewPanelCoords, setReviewPanelCoords] = useState<{
        top?: number;
        left?: number;
        right?: number;
        bottom?: number;
    }>({ top: 0, left: 0 });
    const [reviewPanelFullCode, setReviewPanelFullCode] = useState<
        Course["id"] | null
    >(null);
    const ref = useRef(null);

    const [expandedCoursesPanelCoords, setExpandedCoursesPanelCoords] = useState<{
        top?: number;
        left?: number;
        right?: number;
        bottom?: number;
    }>({ top: 0, left: 0 });
    const [expandedCoursesPanelCourses, setExpandedCoursesPanelCourses] = useState<
        Fulfillment[] | null | undefined
    >(null);

    const [retract, setRetract] = useState<(() => void)>(() => () => console.log('this is a placeholder'));
    const [open, setOpen] = useState<boolean>(false);
    const [ruleId, setRuleId] = useState<number | null>(null);
    const [searchRef, setSearchRef] = useState<MutableRefObject<any> | null>(null);

    const semesterRefs = React.useRef<{ [semester: string]: HTMLDivElement | null }>({});

    // Scroll to current semester
    useEffect(() => {
        if (options?.SEMESTER) {
            const ref = semesterRefs.current[options.SEMESTER];
            if (ref) {
                ref.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }
    }, [semesterRefs]);

    // search panel
    const [searchPanelOpen, setSearchPanelOpen] = useState<boolean>(false);
    const [searchRuleId, setSearchRuleId] = useState<Rule["id"] | null>(null);
    const [searchRuleQuery, setSearchRuleQuery] = useState<string | null>(null); // a query object
    const [searchFulfillments, setSearchFulfillments] = useState<Fulfillment[]>([]); // fulfillments matching the ruleId

    const updateOnboardedFlag = async () => {
        try {
            const url = `/accounts/me/`;

            const res = await fetch(url, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrf() as string,
                },
                body: JSON.stringify({
                    first_name: user.first_name,
                    last_name: user.last_name,
                    profile: { ...user.profile, has_been_onboarded: true },
                }),
            });

            if (!res.ok) {
                return;
            }
        } catch (err) {
            console.error("Error updating user:", err);
        }
    };



    return (
        <>
            <>
                <SearchPanelContext.Provider
                    value={{
                        setSearchPanelOpen,
                        searchPanelOpen,
                        setSearchRuleId,
                        searchRuleId,
                        setSearchRuleQuery,
                        searchRuleQuery,
                        setSearchFulfillments,
                        searchFulfillments
                    }}
                >
                    <ReviewPanelContext.Provider
                        value={{
                            full_code: reviewPanelFullCode,
                            set_full_code: setReviewPanelFullCode,
                            position: reviewPanelCoords,
                            setPosition: setReviewPanelCoords,
                        }}
                    >
                        <ExpandedCoursesPanelContext.Provider
                            value={{
                                courses: expandedCoursesPanelCourses,
                                set_courses: setExpandedCoursesPanelCourses,
                                position: expandedCoursesPanelCoords,
                                setPosition: setExpandedCoursesPanelCoords,
                                retract: retract,
                                set_retract: setRetract,
                                open: open,
                                set_open: setOpen,
                                rule_id: ruleId,
                                set_rule_id: setRuleId,
                                search_ref: searchRef,
                                set_search_ref: setSearchRef,
                                degree_plan_id: activeDegreeplan?.id
                            }}
                        >
                            <TutorialModalContext.Provider
                                value={{
                                    tutorialModalKey: tutorialModalKey,
                                    setTutorialModalKey: setTutorialModalKey,
                                    highlightedComponentRef: highlightedComponentRef,
                                    componentRefs: componentRefs,
                                }}
                            >
                                <SemestersContext.Provider value={{
                                    semesterRefs: semesterRefs
                                }}>
                                    {showTutorialModal && <TutorialModal updateOnboardingFlag={updateOnboardedFlag} />}
                                    {reviewPanelFullCode && (
                                        <ReviewPanel
                                            currentSemester={options?.SEMESTER}
                                            full_code={reviewPanelFullCode}
                                            set_full_code={setReviewPanelFullCode}
                                            position={reviewPanelCoords}
                                            setPosition={setReviewPanelCoords}
                                        />
                                    )}
                                    {expandedCoursesPanelCourses && (
                                        <ExpandedCoursesPanel
                                            currentSemester={options?.SEMESTER}
                                            courses={expandedCoursesPanelCourses}
                                            set_courses={setExpandedCoursesPanelCourses}
                                            position={expandedCoursesPanelCoords}
                                            setPosition={setExpandedCoursesPanelCoords}
                                            retract={retract}
                                            set_retract={setRetract}
                                            open={open}
                                            set_open={setOpen}
                                            rule_id={ruleId}
                                            set_rule_id={setRuleId}
                                            search_ref={searchRef}
                                            set_search_ref={setSearchRef}
                                            degree_plan_id={activeDegreeplan?.id}
                                        />
                                    )}
                                    {modalKey && (
                                        <DegreeModal
                                            setModalKey={setModalKey}
                                            modalKey={modalKey}
                                            modalObject={modalObject}
                                            activeDegreePlan={activeDegreeplan}
                                            setActiveDegreeplan={setActiveDegreeplan}
                                        />
                                    )}
                                    <PageContainer>
                                        <BodyContainer ref={ref}>
                                            {!!showOnboardingModal ? (
                                                <OnboardingPage
                                                    setShowOnboardingModal={setShowOnboardingModal}
                                                    setActiveDegreeplan={setActiveDegreeplan}
                                                />
                                            ) : (
                                                <Row>
                                                    {/*
                // @ts-ignore */}
                                                    <SplitPane
                                                        split="vertical"
                                                        maxSize={searchPanelOpen ?
                                                            (windowWidth ? windowWidth : 1000) * 0.5
                                                            : (windowWidth ? windowWidth : 1000) * 0.66}
                                                        minSize={(windowWidth ? windowWidth : 400) * 0.33}
                                                        defaultSize="50%"
                                                        style={{
                                                            padding: "1.5rem",
                                                            paddingBottom: "1rem" // less padding on bottom for penn labs footer
                                                        }}
                                                    >
                                                        {/*
                        <SplitPane
                          split="vertical"
                          maxSize={searchPanelOpen ?
                            (windowWidth ? windowWidth : 1000) * 0.5
                            : (windowWidth ? windowWidth : 1000) * 0.66}
                          minSize={(windowWidth ? windowWidth : 400) * 0.33}
                          defaultSize="50%"
                          style={{
                            padding: "1.5rem",
                            paddingBottom: "1rem" // less padding on bottom for penn labs footer
                          }}
                        >
                          {/*
                  // @ts-ignore */}
                                                        <PanelWrapper>
                                                            <PanelInteriorWrapper>
                                                                <PlanPanel
                                                                    currentSemester={options?.SEMESTER}
                                                                    setModalKey={setModalKey}
                                                                    modalKey={modalKey}
                                                                    setModalObject={setModalObject}
                                                                    isLoading={
                                                                        isLoadingDegreeplans // || isLoadingActiveDegreePlan
                                                                    }
                                                                    activeDegreeplan={activeDegreeplan}
                                                                    degreeplans={degreeplans}
                                                                    setActiveDegreeplan={setActiveDegreeplan}
                                                                    setShowOnboardingModal={setShowOnboardingModal}
                                                                />
                                                            </PanelInteriorWrapper>
                                                        </PanelWrapper>
                                                        {/*
                  // @ts-ignore */}
                                                        <PanelWrapper>
                                                            <PanelInteriorWrapper>
                                                                <ReqPanel
                                                                    setModalKey={setModalKey}
                                                                    setModalObject={setModalObject}
                                                                    isLoading={isLoadingDegreeplans}
                                                                    activeDegreeplan={activeDegreeplan}
                                                                />
                                                            </PanelInteriorWrapper>
                                                            {searchPanelOpen && (
                                                                <PanelInteriorWrapper $minWidth={"48%"} $maxWidth={"48%"}>
                                                                    <SearchPanel activeDegreeplanId={activeDegreeplan ? activeDegreeplan.id : null} />
                                                                </PanelInteriorWrapper>
                                                            )}
                                                        </PanelWrapper>
                                                    </SplitPane>
                                                </Row>
                                            )}
                                        </BodyContainer>
                                        <Footer />
                                        <Dock user={user} login={updateUser} logout={() => updateUser(null)} activeDegreeplanId={activeDegreeplan ? activeDegreeplan.id : null} />
                                    </PageContainer>
                                </SemestersContext.Provider>
                            </TutorialModalContext.Provider>
                        </ExpandedCoursesPanelContext.Provider>
                    </ReviewPanelContext.Provider>
                </SearchPanelContext.Provider>
            </>
        </>
    );
};

export default FourYearPlanPage;
