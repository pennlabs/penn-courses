import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";
import React, { useEffect, useState } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';
import { EditButton } from './EditButton';
import { PanelTopBarButton, PanelTopBarIcon } from "./PanelCommon";
import { PanelContainer, PanelHeader, PanelTopBarIconList, PanelBody } from "./PanelCommon";

const ShowStatsWrapper = styled(PanelTopBarButton)`
    min-width: 9rem;
`

const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean) => void }) => (
    <ShowStatsWrapper onClick={() => setShowStats(!showStats)}>
        <PanelTopBarIcon>
            <i className={`fas fa-md fa-chart-bar ${showStats ? "" : "icon-crossed-out"}`}/>
        </PanelTopBarIcon>
        <div>
            {showStats ? "Hide Stats" : "Show Stats"}
        </div>
    </ShowStatsWrapper>
);

interface PlanPanelProps {
    setModalKey: (arg0: string) => void;
    modalKey: string;
    setModalObject: (arg0: DegreePlan | null) => void;
    setActiveDegreeplan: (arg0: DegreePlan | null) => void;
    activeDegreeplan: DegreePlan | null;
    degreeplans: DegreePlan[] | undefined;
    isLoading: boolean;
    currentSemester: string;
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
    currentSemester
} : PlanPanelProps) => {
    const { copy: copyDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
    const [showStats, setShowStats] = useState(true);
    const [editMode, setEditMode] = useState(false);

    return (
            <PanelContainer>
                <PanelHeader>
                    <SelectListDropdown
                        itemType="degree plan" 
                        active={activeDegreeplan}
                        getItemName={(item: DegreePlan) => item.name}
                        allItems={degreeplans || []} 
                        selectItem={(id: DegreePlan["id"]) => setActiveDegreeplan(degreeplans?.filter(d => d.id === id)[0])}
                        mutators={{
                            copy: (item: DegreePlan) => {
                                (copyDegreeplan({...item, name: `${item.name} (copy)`}, item.id) as Promise<any>)
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
                                /** When a semester is created, 
                                 * if there is no localStorage.getItem('PDP-start-grad-years'), 
                                 * the onboarding page will pop up which then sets PDP-start-grad-years
                                 * in localStorage */
                                if (typeof window !== "undefined" && !!localStorage.getItem('PDP-start-grad-years'))
                                    setModalKey("plan-create")
                                else setShowOnboardingModal(true);
                            }
                        }}
                        isLoading={isLoading} 
                    />
                    <PanelTopBarIconList>
                        <ShowStatsButton showStats={showStats} setShowStats={setShowStats} />
                        <EditButton editMode={editMode} setEditMode={setEditMode} />
                    </PanelTopBarIconList>
                </PanelHeader>
                {/** map to semesters */}
                <PanelBody>
                    <Semesters 
                    activeDegreeplan={activeDegreeplan} 
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
}

export default PlanPanel;