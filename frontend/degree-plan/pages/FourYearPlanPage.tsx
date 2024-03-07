import React, { useState, useEffect, useRef } from "react";
import ReqPanel from "../components/Requirements/ReqPanel";
import PlanPanel from "../components/FourYearPlan/PlanPanel";
import {
  SearchPanel,
  SearchPanelContext,
} from "../components/Search/SearchPanel";
// import Plan from "../components/example/Plan";
import styled from "@emotion/styled";
import useSWR, { useSWRConfig } from "swr";
import { Course, DegreePlan, Options, Rule } from "@/types";
import ReviewPanel from "@/components/Infobox/ReviewPanel";
import { ReviewPanelContext } from "@/components/Infobox/ReviewPanel";
import DegreeModal, { ModalKey } from "@/components/FourYearPlan/DegreeModal";
import SplitPane, { Pane } from "react-split-pane";
import Dock from "@/components/Dock/Dock";
import useWindowDimensions from "@/hooks/window";
import OnboardingPage from "./OnboardingPage";

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
  background-color: var(--background-blue-grey);
  width: 100%;
  flex-grow: 1;
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

const PanelWrapper = styled.div<{ $maxWidth: string; $minWidth: string }>`
  border-radius: 10px;
  box-shadow: 0px 0px 8px 0px #00000026;
  overflow: hidden; /* Hide scrollbars */
  width: ${(props) => (props.$maxWidth || props.$maxWidth ? "auto" : "100%")};
  max-width: ${(props) => (props.$maxWidth ? props.$maxWidth : "auto")};
  min-width: ${(props) => (props.$minWidth ? props.$minWidth : "auto")};
  position: relative;
  height: 100%;
`;

const FourYearPlanPage = ({
  updateUser,
  user,
  activeDegreeplanId,
  setActiveDegreeplanId,
}: any) => {
  // edit modals for degree and degree plan
  const [modalKey, setModalKey] = useState<ModalKey>(null);
  const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // stores the which degreeplan is being updated using the modal
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);

    const { data: degreeplans, isLoading: isLoadingDegreeplans } = useSWR<
    DegreePlan[]
  >("/api/degree/degreeplans");
  const { data: activeDegreePlan, isLoading: isLoadingActiveDegreePlan } =
    useSWR(
      activeDegreeplanId
        ? `/api/degree/degreeplans/${activeDegreeplanId}`
        : null
    );

  useEffect(() => {
    console.log("FIRED", degreeplans)
    // recompute the active degreeplan id on changes to the degreeplans
    if (!isLoadingDegreeplans && !degreeplans?.length) {
      setShowOnboardingModal(true);
    }
    if (!degreeplans?.length) {
      setActiveDegreeplanId(null);
    } else if (
      !activeDegreeplanId ||
      !degreeplans.find((d) => d.id === activeDegreeplanId)
    ) {
      const mostRecentUpdated = degreeplans.reduce((a, b) =>
        a.updated_at > b.updated_at ? a : b
      );
      setActiveDegreeplanId(mostRecentUpdated.id);
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
    Course["full_code"] | null
  >(null);
  const ref = useRef(null);

  // search panel
  const [searchPanelOpen, setSearchPanelOpen] = useState<boolean>(false);
  const [searchRuleId, setSearchRuleId] = useState<Rule["id"] | null>(null);
  const [searchRuleQuery, setSearchRuleQuery] = useState<string | null>(null); // a query object 

  return (
    <SearchPanelContext.Provider
      value={{
        setSearchPanelOpen: setSearchPanelOpen,
        searchPanelOpen: searchPanelOpen,
        setSearchRuleId: setSearchRuleId,
        searchRuleId: searchRuleId,
        setSearchRuleQuery: setSearchRuleQuery,
        searchRuleQuery: searchRuleQuery,
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
                <SplitPane
                  split="vertical"
                  minSize={0}
                  maxSize={windowWidth ? windowWidth * 0.65 : 1000}
                  defaultSize="50%"
                  style={{
                    padding: "2rem"
                  }}
                >
                <PanelWrapper>
                  <PlanPanel
                    setModalKey={setModalKey}
                    modalKey={modalKey}
                    setModalObject={setModalObject}
                    isLoading={
                      isLoadingDegreeplans || isLoadingActiveDegreePlan
                    }
                    activeDegreeplan={activeDegreePlan}
                    degreeplans={degreeplans}
                    setActiveDegreeplanId={setActiveDegreeplanId}
                  />
                </PanelWrapper>
                <PanelWrapper>
                  <ReqPanel
                    setModalKey={setModalKey}
                    setModalObject={setModalObject}
                    isLoading={isLoadingActiveDegreePlan}
                    activeDegreeplan={activeDegreePlan}
                  />
                </PanelWrapper>
                {searchPanelOpen && (
                  <PanelWrapper $minWidth={"40%"} $maxWidth={"45%"}>
                    <SearchPanel activeDegreeplanId={activeDegreeplanId} />
                  </PanelWrapper>
                )}
                </SplitPane>
              </Row>
            )}
          </BodyContainer>
          <Dock user={user} login={updateUser} logout={() => updateUser(null)} />
        </PageContainer>
      </ReviewPanelContext.Provider>
    </SearchPanelContext.Provider>
  );
};

export default FourYearPlanPage;
