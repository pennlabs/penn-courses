import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  MutableRefObject,
} from "react";
import ReqPanel from "./Requirements/ReqPanel";
import PlanPanel from "./FourYearPlan/PlanPanel";
import { SearchPanel, SearchPanelContext } from "./Search/SearchPanel";
import styled from "@emotion/styled";
import useSWR from "swr";
import {
  Course,
  DegreePlan,
  DockedCourse,
  Fulfillment,
  Options,
  Rule,
  User,
} from "@/types";
import ReviewPanel from "@/components/Infobox/ReviewPanel";
import { ReviewPanelContext } from "@/components/Infobox/ReviewPanel";
import DegreeModal, { ModalKey } from "@/components/FourYearPlan/DegreeModal";
import SplitColumns from "@/components/common/SplitColumns";
import Dock from "@/components/Dock/Dock";
import TopBar from "@/components/TopBar";
import useStickyState from "@/hooks/stickyState";
import OnboardingPage from "../pages/OnboardingPage";
import EditProgramsPanel from "@/components/OnboardingPanels/EditProgramsPanel";
import Footer from "./Footer";
import PhoneTabBar, { PHONE_TABS, PhoneTab } from "./mobile/PhoneTabBar";
import PhoneSwiper from "./mobile/PhoneSwiper";
import DockedPanel from "./mobile/DockedPanel";
import useIsPhone from "@/hooks/useIsPhone";

import ExpandedCoursesPanel from "@/components/ExpandedBox/ExpandedCoursesPanel";
import { ExpandedCoursesPanelContext } from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";
import { POPOVER_BOUNDS_ATTRIBUTE } from "@/components/Course/Course";
import { PlanSemestersContext } from "@/components/FourYearPlan/PlanSemestersContext";

const PageContainer = styled.div`
  height: 100vh;
  /* iOS Safari's 100vh includes the space under its toolbars. */
  height: 100dvh;
  width: 100vw;
  display: flex;
  flex-direction: column;
`;

// Absolutely positioned so that the columns scroll inside the body instead of sizing it.
const Row = styled.div`
  position: absolute;
  inset: 0;
  padding: 1.5rem 1.5rem 1rem; /* less padding on bottom for penn labs footer */

  /* PhoneSwiper pads each slide instead. */
  @media (max-width: 767px) {
    padding: 0;
  }
`;

const BodyContainer = styled.div`
  background-color: var(--background-light-grey);
  width: 100%;
  flex-grow: 1;
  position: relative;
  /* Keeps the panels' sticky headers and popovers from stacking over the top bar's account menu. */
  isolation: isolate;
`;

const PanelInteriorWrapper = styled.div`
  border-radius: 10px;
  box-shadow: 0px 0px 5px 1px #00000026;
  overflow: hidden; /* Hide scrollbars */
  width: 100%;
  position: relative;
  height: 100%;
`;

const DEFAULT_COLUMN_WIDTHS = {
  "plan+requirements": [62, 38],
  "plan+search": [70, 30],
  "requirements+search": [72, 28],
  "plan+requirements+search": [48, 26, 26],
};

type FourYearPlanPageProps = {
  updateUser: (newUserVal: User | null) => void;
  user: User | null;
};

const FourYearPlanPage = ({ updateUser, user }: FourYearPlanPageProps) => {
  // Stable identity so the account indicator's login-check effect doesn't rerun every render.
  const logout = useCallback(() => updateUser(null), [updateUser]);

  // edit modals for degree and degree plan
  const [modalKey, setModalKey] = useState<ModalKey>(null);
  const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // stores the which degreeplan is being updated using the modal
  const [showOnboardingModal, setShowOnboardingModal] = useState(false);
  const [editingPrograms, setEditingPrograms] = useState(false);
  const [
    activeDegreeplan,
    setActiveDegreeplan,
  ] = React.useState<DegreePlan | null>(null);

  // Degree plan endpoints require login, so wait for the user before requesting them.
  // Firing early only produced a burst of 403 toasts on every reload.
  const { data: degreeplans, isLoading: isLoadingDegreeplans } = useSWR<
    DegreePlan[]
  >(user ? "/api/degree/degreeplans" : null);

  useEffect(() => {
    // recompute the active degreeplan id on changes to the degreeplans
    // Only an empty list means the user has no plans; a failed request leaves data undefined.
    if (!isLoadingDegreeplans && degreeplans && !degreeplans.length) {
      setShowOnboardingModal(true);
    }
    if (!degreeplans?.length) {
      setActiveDegreeplan(null);
    } else if (
      !activeDegreeplan ||
      !degreeplans.find((d) => d.id === activeDegreeplan.id)
    ) {
      const mostRecentUpdated = degreeplans.reduce((a, b) =>
        a.updated_at > b.updated_at ? a : b
      );
      setActiveDegreeplan(mostRecentUpdated);
    }
  }, [degreeplans, isLoadingDegreeplans]);

  const [planOpen, setPlanOpen] = useStickyState("PDP-plan-column-open", true);
  const [requirementsOpen, setRequirementsOpen] = useStickyState(
    "PDP-requirements-column-open",
    true
  );

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
  const [
    expandedCoursesPanelCourses,
    setExpandedCoursesPanelCourses,
  ] = useState<Fulfillment[] | null | undefined>(null);

  const [retract, setRetract] = useState<() => void>(() => () =>
    console.log("this is a placeholder")
  );
  const [open, setOpen] = useState<boolean>(false);
  const [ruleId, setRuleId] = useState<number | null>(null);
  const [searchRef, setSearchRef] = useState<MutableRefObject<any> | null>(
    null
  );

  // search panel
  const [searchPanelOpen, setSearchPanelOpen] = useState<boolean>(false);
  const [searchRuleId, setSearchRuleId] = useState<Rule["id"] | null>(null);
  const [searchRuleQuery, setSearchRuleQuery] = useState<string | null>(null); // a query object
  const [planSemesters, setPlanSemesters] = useState<string[]>([]);
  const [searchFulfillments, setSearchFulfillments] = useState<Fulfillment[]>(
    []
  ); // fulfillments matching the ruleId

  const isPhone = useIsPhone();
  const [phoneTab, setPhoneTab] = useState<PhoneTab>("plan");
  const lastPhoneTab = useRef<PhoneTab>("plan");
  useEffect(() => {
    if (searchPanelOpen) setPhoneTab("search");
    else setPhoneTab((tab) => (tab === "search" ? lastPhoneTab.current : tab));
  }, [searchPanelOpen]);
  const selectPhoneTab = (tab: PhoneTab) => {
    if (tab === "search") {
      setSearchRuleQuery("");
      setSearchRuleId(null);
      setSearchPanelOpen(true);
      return;
    }
    lastPhoneTab.current = tab;
    setSearchPanelOpen(false);
    setPhoneTab(tab);
  };
  const { data: dockedCourses } = useSWR<DockedCourse[]>(
    user ? "/api/degree/docked" : null
  );

  const planPanel = (
    <PanelInteriorWrapper>
      <PlanPanel
        currentSemester={options?.SEMESTER}
        setModalKey={setModalKey}
        modalKey={modalKey}
        setModalObject={setModalObject}
        isLoading={isLoadingDegreeplans}
        activeDegreeplan={activeDegreeplan}
        degreeplans={degreeplans}
        setActiveDegreeplan={setActiveDegreeplan}
        setShowOnboardingModal={setShowOnboardingModal}
        footer={isPhone && <Footer />}
      />
    </PanelInteriorWrapper>
  );
  const requirementsPanel = (
    <PanelInteriorWrapper>
      <ReqPanel
        isLoading={isLoadingDegreeplans}
        activeDegreeplan={activeDegreeplan}
        onEditPrograms={() => setEditingPrograms(true)}
      />
    </PanelInteriorWrapper>
  );
  // Unmounted when closed, so that it focuses its input each time it opens.
  const searchPanel = searchPanelOpen && (
    <PanelInteriorWrapper>
      <SearchPanel
        activeDegreeplanId={activeDegreeplan ? activeDegreeplan.id : null}
      />
    </PanelInteriorWrapper>
  );
  const phonePanels: Record<PhoneTab, React.ReactNode> = {
    plan: planPanel,
    requirements: requirementsPanel,
    search: searchPanel,
    docked: (
      <PanelInteriorWrapper>
        <DockedPanel user={user} />
      </PanelInteriorWrapper>
    ),
  };

  return (
    <PlanSemestersContext.Provider
      value={{ semesters: planSemesters, setSemesters: setPlanSemesters }}
    >
      <SearchPanelContext.Provider
        value={{
          setSearchPanelOpen,
          searchPanelOpen,
          setSearchRuleId,
          searchRuleId,
          setSearchRuleQuery,
          searchRuleQuery,
          setSearchFulfillments,
          searchFulfillments,
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
              setCourses: setExpandedCoursesPanelCourses,
              position: expandedCoursesPanelCoords,
              setPosition: setExpandedCoursesPanelCoords,
              retract: retract,
              set_retract: setRetract,
              open: open,
              setOpen: setOpen,
              ruleId: ruleId,
              setRuleId: setRuleId,
              searchRef: searchRef,
              setSearchRef: setSearchRef,
              degreePlanId: activeDegreeplan?.id,
            }}
          >
            {reviewPanelFullCode && (
              <ReviewPanel
                currentSemester={options?.SEMESTER}
                degreePlanId={activeDegreeplan?.id}
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
                setCourses={setExpandedCoursesPanelCourses}
                position={expandedCoursesPanelCoords}
                setPosition={setExpandedCoursesPanelCoords}
                retract={retract}
                set_retract={setRetract}
                open={open}
                setOpen={setOpen}
                ruleId={ruleId}
                setRuleId={setRuleId}
                searchRef={searchRef}
                setSearchRef={setSearchRef}
                degreePlanId={activeDegreeplan?.id}
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
            {editingPrograms && activeDegreeplan && (
              <EditProgramsPanel
                degreePlanId={activeDegreeplan.id}
                onClose={() => setEditingPrograms(false)}
              />
            )}
            <PageContainer>
              <TopBar
                user={user}
                login={updateUser}
                logout={logout}
                planOpen={planOpen}
                setPlanOpen={setPlanOpen}
                requirementsOpen={requirementsOpen}
                setRequirementsOpen={setRequirementsOpen}
                showColumnToggles={!showOnboardingModal && !isPhone}
              />
              {/* Course popovers keep within the body, so they never cover the footer or dock. */}
              <BodyContainer
                ref={ref}
                {...{ [POPOVER_BOUNDS_ATTRIBUTE]: true }}
              >
                {!!showOnboardingModal ? (
                  <OnboardingPage
                    setShowOnboardingModal={setShowOnboardingModal}
                    setActiveDegreeplan={setActiveDegreeplan}
                    canExit={!!degreeplans?.length}
                  />
                ) : (
                  <Row>
                    {isPhone ? (
                      <PhoneSwiper
                        tabs={PHONE_TABS}
                        active={phoneTab}
                        onChange={selectPhoneTab}
                        panels={phonePanels}
                      />
                    ) : (
                      <SplitColumns
                        storageKey="PDP-column-widths"
                        defaultWidths={DEFAULT_COLUMN_WIDTHS}
                        emptyState="Open Plan or Requirements from the top bar to show a column."
                        columns={[
                          {
                            id: "plan",
                            label: "plan",
                            visible: planOpen,
                            content: planPanel,
                          },
                          {
                            id: "requirements",
                            label: "requirements",
                            visible: requirementsOpen,
                            content: requirementsPanel,
                          },
                          {
                            id: "search",
                            label: "search",
                            visible: searchPanelOpen,
                            content: searchPanel,
                          },
                        ]}
                      />
                    )}
                  </Row>
                )}
              </BodyContainer>
              {isPhone ? (
                !showOnboardingModal && (
                  <PhoneTabBar
                    active={phoneTab}
                    onSelect={selectPhoneTab}
                    dockedCount={dockedCourses?.length ?? 0}
                  />
                )
              ) : (
                <>
                  <Footer />
                  <Dock
                    user={user}
                    activeDegreeplanId={
                      activeDegreeplan ? activeDegreeplan.id : null
                    }
                  />
                </>
              )}
            </PageContainer>
          </ExpandedCoursesPanelContext.Provider>
        </ReviewPanelContext.Provider>
      </SearchPanelContext.Provider>
    </PlanSemestersContext.Provider>
  );
};

export default FourYearPlanPage;
