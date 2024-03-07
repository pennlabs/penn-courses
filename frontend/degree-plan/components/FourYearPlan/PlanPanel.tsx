import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";
import React, { useState } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'
import { EditButton } from './EditButton';
import { PanelTopBarButton, PanelTopBarIcon } from "./PanelTopBarCommon";

const ShowStatsWrapper = styled(PanelTopBarButton)`
    min-width: 8.75rem;
`

export const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean) => void }) => (
    <ShowStatsWrapper onClick={() => setShowStats(!showStats)}>
        <PanelTopBarIcon>
            <i className={`fas fa-md fa-chart-bar ${showStats ? "" : "icon-crossed-out"}`}/>
        </PanelTopBarIcon>
        <div>
            {showStats ? "Hide Stats" : "Show Stats"}
        </div>
    </ShowStatsWrapper>
);

export const DarkBlueBackgroundSkeleton: React.FC<{ width: string }> = (props) => (
    <Skeleton
    baseColor="var(--primary-color-dark)"
    {...props}
    />
)

export const PanelHeader = styled.div`
    display: flex;
    justify-content: space-between;
    background-color: var(--primary-color);
    padding: 0.5rem 1rem;
    flex-grow: 0;
    font-weight: 300;
`;

export const PanelBody = styled.div`
    padding: 1.5rem;
    height: 100%;
    overflow-y: auto;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;

export const PanelContainer = styled.div`
    border-radius: 10px;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
`;

export const PanelTopBarIconList = styled.div`
    display: flex;
    flex-direction: row;
    gap: 0.8rem;
`

interface PlanPanelProps {
    setModalKey: (arg0: string) => void;
    modalKey: string;
    setModalObject: (arg0: DegreePlan | null) => void;
    setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
    activeDegreeplan: DegreePlan | undefined;
    degreeplans: DegreePlan[] | undefined;
    isLoading: boolean;
}

const PlanPanel = ({ 
    setModalKey,
    modalKey,
    setModalObject,
    setActiveDegreeplanId,
    activeDegreeplan,
    degreeplans,
    isLoading 
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
                        selectItem={(id: DegreePlan["id"]) => setActiveDegreeplanId(id)}
                        mutators={{
                            copy: (item: DegreePlan) => {
                                (copyDegreeplan({...item, name: `${item.name} (copy)`}, item.id) as Promise<any>)
                                .then((copied) => copied && setActiveDegreeplanId(copied.id))
                            },
                            remove: (item: DegreePlan) => {
                                setModalKey("plan-remove")
                                setModalObject(item)
                            },
                            rename: (item: DegreePlan) => {
                                setModalKey("plan-rename")
                                setModalObject(item)
                            },
                            create: () => setModalKey("plan-create")
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
                    setModalKey={setModalKey}
                    setModalObject={setModalObject}
                    isLoading={isLoading}
                    />
                </PanelBody>
            </PanelContainer>
    );
}

export default PlanPanel;