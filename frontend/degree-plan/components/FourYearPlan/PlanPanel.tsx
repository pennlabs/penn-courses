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
    modalKey,
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
        if (!planPanelRef.current || !componentRefs || !('current' in componentRefs)) return;
        const activeKeys = ["calendar-panel", "current-semester", "future-semesters", "past-semesters", "edit-mode", "show-stats"];
        if (activeKeys.includes(tutorialModalKey || '')) {
            planPanelRef.current.style.zIndex = "11";
            componentRefs.current["planPanel"] = planPanelRef.current;
        } else {
            planPanelRef.current.style.zIndex = "0";
        }
        if (showStatsRef.current && tutorialModalKey === 'show-stats') {
            componentRefs.current['showStatsButton'] = showStatsRef.current;
        }
        if (editSemesterRef.current && tutorialModalKey === 'edit-mode') {
            componentRefs.current['editSemesterButton'] = editSemesterRef.current;
        }
    }, [tutorialModalKey, componentRefs]);

    useEffect(() => {
        if (tutorialModalKey !== 'current-semester') return;
        if (!currentSemester) return;
        let attempts = 0;
        const maxAttempts = 10;
        const attemptScroll = () => {
            attempts++;
            const target = semesterRefs?.current?.[currentSemester];
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
            } else if (attempts < maxAttempts) {
                setTimeout(attemptScroll, 120);
            }
        };
        // slight delay to allow modal and semesters render
        const startTimer = setTimeout(attemptScroll, 50);
        return () => clearTimeout(startTimer);
    }, [tutorialModalKey, currentSemester, semesterRefs]);

    return (
        <PanelContainer style={{ position: "relative" }} ref={(el) => {
            planPanelRef.current = el;
            if (!componentRefs || !('current' in componentRefs)) return;
            if (tutorialModalKey === "calendar-panel" || tutorialModalKey === "current-semester" || tutorialModalKey === "future-semesters" || tutorialModalKey === "past-semesters" || tutorialModalKey === "edit-mode" || tutorialModalKey === "show-stats") {
                componentRefs.current["planPanel"] = el;
            }
        }}>
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
                    <TutorialHighlight $active={tutorialModalKey === 'show-stats'} ref={(el) => { showStatsRef.current = el; if (el && componentRefs && ('current' in componentRefs) && tutorialModalKey === 'show-stats') { componentRefs.current['showStatsButton'] = el; } }}>
                        <ShowStatsButton showStats={showStats} setShowStats={setShowStats} />
                    </TutorialHighlight>
                    <TutorialHighlight $active={tutorialModalKey === 'edit-mode'} ref={(el) => { editSemesterRef.current = el; if (el && componentRefs && ('current' in componentRefs) && tutorialModalKey === 'edit-mode') { componentRefs.current['editSemesterButton'] = el; } }}>
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