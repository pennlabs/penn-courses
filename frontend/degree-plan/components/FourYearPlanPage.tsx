import React, { useState, useEffect, useRef, useCallback, createContext } from "react";
import ReqPanel from "./Requirements/ReqPanel";
import PlanPanel from "./FourYearPlan/PlanPanel";
import {
  SearchPanel,
  SearchPanelContext,
} from "./Search/SearchPanel";
// import Plan from "../components/example/Plan";
import styled from "@emotion/styled";
import useSWR, { useSWRConfig } from "swr";
import { Course, DegreePlan, Fulfillment, Options, Rule } from "@/types";
import ReviewPanel from "@/components/Infobox/ReviewPanel";
import { ReviewPanelContext } from "@/components/Infobox/ReviewPanel";
import DegreeModal, { ModalKey } from "@/components/FourYearPlan/DegreeModal";
import SplitPane, { Pane } from "react-split-pane";
import Dock from "@/components/Dock/Dock";
import useWindowDimensions from "@/hooks/window";
import OnboardingPage from "../pages/OnboardingPage";
import Footer from "./Footer";
import { expectedDoubleCounts } from "@/utils";

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
  gap: 2rem;
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

export const ExpectedDoubleCountsContext = createContext<ReturnType<typeof expectedDoubleCounts>>(() => ([]))

const FourYearPlanPage = ({
  updateUser,
  user
}: any) => {
  // edit modals for degree and degree plan
  const [modalKey, setModalKey] = useState<ModalKey>(null);
  const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // stores the which degreeplan is being updated using the modal
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);
  const [activeDegreeplanId, setActiveDegreeplanId] = React.useState<DegreePlan["id"] | null>(null);

  const { data: degreeplans, isLoading: isLoadingDegreeplans } = useSWR<
    DegreePlan[]
  >("/api/degree/degreeplans");
  useEffect(() => {
    // recompute the active degreeplan id on changes to the degreeplans
    if (!isLoadingDegreeplans && !degreeplans?.length) {
      setShowOnboardingModal(true);
    }
    if (!degreeplans?.length) {
      setActiveDegreeplanId(null);
    } else if (
      !activeDegreeplanId || !degreeplans.find((d) => d.id === activeDegreeplanId)
    ) {
      const mostRecentUpdated = degreeplans.reduce((a, b) =>
        a.updated_at > b.updated_at ? a : b
      );
      setActiveDegreeplanId(mostRecentUpdated.id);
    }
  }, [degreeplans, isLoadingDegreeplans]);
  const { data: activeDegreeplan, isLoading: isLoadingActiveDegreeplan } = useSWR<
    DegreePlan
  >(activeDegreeplanId !== null ? `/api/degree/degreeplans/${activeDegreeplanId}` : null);

  const getExpectedDoubleCounts = useCallback((expectedDoubleCounts(activeDegreeplan)), [activeDegreeplan])

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

  // search panel
  const [searchPanelOpen, setSearchPanelOpen] = useState<boolean>(false);
  const [searchRuleId, setSearchRuleId] = useState<Rule["id"] | null>(null);
  const [searchRuleQuery, setSearchRuleQuery] = useState<string | null>(null); // a query object
  const [searchFulfillments, setSearchFulfillments] = useState<Fulfillment[]>([]); // fulfillments matching the ruleId

  return (
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
        <ExpectedDoubleCountsContext.Provider value={getExpectedDoubleCounts}>
          {reviewPanelFullCode && (
            <ReviewPanel
              currentSemester={options?.SEMESTER}
              full_code={reviewPanelFullCode}
              set_full_code={setReviewPanelFullCode}
              position={reviewPanelCoords}
              setPosition={setReviewPanelCoords}
            />
          )}
          {modalKey && (
            <DegreeModal
              setModalKey={setModalKey}
              modalKey={modalKey}
              modalObject={modalObject}
              setActiveDegreeplanId={setActiveDegreeplanId}
            />
          )}
          <PageContainer>
            <BodyContainer ref={ref}>
              {!!showOnboardingModal ? (
                <OnboardingPage
                  setShowOnboardingModal={setShowOnboardingModal}
                  setActiveDegreeplanId={setActiveDegreeplanId}
                />
              ) : (
                <Row>
                  {/*
                  // @ts-ignore */}
                  <SplitPane
                    split="vertical"
                    maxSize={windowWidth ? windowWidth * 0.65 : 1000}
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
                          setActiveDegreeplanId={setActiveDegreeplanId}
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
                        <PanelInteriorWrapper $minWidth={"40%"} $maxWidth={"45%"}>
                          <SearchPanel activeDegreeplanId={activeDegreeplanId} />
                        </PanelInteriorWrapper>
                      )}
                    </PanelWrapper>
                  </SplitPane>
                </Row>
              )}
            </BodyContainer>
            <Footer />
            <Dock user={user} login={updateUser} logout={() => updateUser(null)} activeDegreeplanId={activeDegreeplanId} />
          </PageContainer>
        </ExpectedDoubleCountsContext.Provider>
      </ReviewPanelContext.Provider>
    </SearchPanelContext.Provider>
  );
};

export default FourYearPlanPage;
