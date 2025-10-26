import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";
import React, { useEffect, useState, useContext } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';
import { EditButton } from './EditButton';
import { PanelTopBarButton, PanelTopBarIcon } from "./PanelCommon";
import { PanelContainer, PanelHeader, PanelTopBarIconList, PanelBody } from "./PanelCommon";
import { ModalKey } from "./DegreeModal";
import { TutorialModalContext } from "./OnboardingTutorial";
import { SemestersContext } from "./Semesters";

const TutorialHighlight = styled.div<{ $active: boolean }>`
  position: relative;
  border-radius: 6px;
  outline: ${p => p.$active ? '2px solid var(--selected-color)' : 'none'};
  outline-offset: 2px;
`

import ToastContext from "../Toast/Toast";

const ShowStatsText = styled.div`
    min-width: 6rem;
`

const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean) => void }) => (
    <PanelTopBarButton onClick={() => setShowStats(!showStats)}>
        <PanelTopBarIcon>
            <i className={`fas fa-md fa-chart-bar ${showStats ? "" : "icon-crossed-out"}`} />
        </PanelTopBarIcon>
        <ShowStatsText>
            {showStats ? "Hide Stats" : "Show Stats"}
        </ShowStatsText>
    </PanelTopBarButton>
);

interface PlanPanelProps {
    setModalKey: (arg0: ModalKey) => void;
    modalKey: string | null;
    setModalObject: (arg0: DegreePlan | null) => void;
    setActiveDegreeplan: (arg0: DegreePlan | null) => void;
    activeDegreeplan: DegreePlan | null;
    degreeplans: DegreePlan[] | undefined;
    isLoading: boolean;
    currentSemester?: string;
    setShowOnboardingModal: (arg0: boolean) => void;
}

const PlanPanel = ({
    setModalKey,
    setModalObject,
    setActiveDegreeplan,
    setShowOnboardingModal,
    activeDegreeplan,
    degreeplans,
    isLoading,
    currentSemester,
}: PlanPanelProps) => {
    const { copy: copyDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
    const [showStats, setShowStats] = useState(true);
    const [editMode, setEditMode] = useState(false);

    const { tutorialModalKey, componentRefs } = useContext(TutorialModalContext);
    const { semesterRefs } = useContext(SemestersContext);
    const planPanelRef = React.useRef<HTMLDivElement | null>(null);
    const showStatsRef = React.useRef<HTMLDivElement | null>(null);
    const editSemesterRef = React.useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (!componentRefs?.current) return;

        if (["calendar-panel", "current-semester", "future-semesters", "past-semesters", "edit-mode", "show-stats"].includes(tutorialModalKey || '')) {
            componentRefs.current["planPanel"] = planPanelRef.current;
            if (planPanelRef.current) {
                planPanelRef.current.style.zIndex = "20";
            }
        } else {
            if (planPanelRef.current) {
                planPanelRef.current.style.zIndex = "";
            }
        }

        if (tutorialModalKey === 'show-stats') {
            componentRefs.current['showStatsButton'] = showStatsRef.current;
        }
        if (tutorialModalKey === 'edit-mode') {
            componentRefs.current['editSemesterButton'] = editSemesterRef.current;
        }
    }, [tutorialModalKey, componentRefs]);

    useEffect(() => {
        if (tutorialModalKey !== 'current-semester') return;
        if (!currentSemester) return;

        const attemptScroll = () => {
            const target = semesterRefs?.current?.[currentSemester];
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
            }
        };
        // slight delay to allow modal and semesters to render
        const startTimer = setTimeout(attemptScroll, 50);
        return () => clearTimeout(startTimer);
    }, [tutorialModalKey, currentSemester, semesterRefs]);

    return (
        <PanelContainer style={{ position: "relative" }} ref={planPanelRef}>
            <PanelHeader>
                <SelectListDropdown
                    itemType="degree plan"
                    active={activeDegreeplan || undefined}
                    getItemName={(item: DegreePlan) => item.name}
                    allItems={degreeplans || []}
                    selectItem={(id: DegreePlan["id"]) => setActiveDegreeplan(degreeplans?.filter(d => d.id === id)[0] || null)}
                    mutators={{
                        copy: (item: DegreePlan) => {
                            (copyDegreeplan({ ...item, name: `${item.name} (copy)` }, item.id) as Promise<any>)
                                .then((copied) => copied && setActiveDegreeplan(copied.id))
                        },
                        remove: (item: DegreePlan) => {
                            setModalKey("plan-remove")
                            setModalObject(item)
                        },
                        rename: (item: DegreePlan) => {
                            setModalKey("plan-rename")
                            setModalObject(item)
                        },
                        create: () => {
                            setShowOnboardingModal(true);
                        }
                    }}
                    isLoading={isLoading}
                />
                <PanelTopBarIconList>
                    <TutorialHighlight $active={tutorialModalKey === 'show-stats'} ref={showStatsRef}>
                        <ShowStatsButton showStats={showStats} setShowStats={setShowStats} />
                    </TutorialHighlight>
                    <TutorialHighlight $active={tutorialModalKey === 'edit-mode'} ref={editSemesterRef}>
                        <EditButton editMode={editMode} setEditMode={setEditMode} />
                    </TutorialHighlight>
                </PanelTopBarIconList>
            </PanelHeader>
            {/** map to semesters */}
            <PanelBody>
                <Semesters
                    activeDegreeplan={activeDegreeplan || undefined}
                    showStats={showStats}
                    editMode={editMode}
                    setEditMode={setEditMode}
                    setModalKey={setModalKey}
                    setModalObject={setModalObject}
                    isLoading={isLoading}
                    currentSemester={currentSemester}
                />
            </PanelBody>
        </PanelContainer>
    );
};

export default PlanPanel;