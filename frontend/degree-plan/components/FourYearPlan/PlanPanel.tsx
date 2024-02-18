import update from 'immutability-helper'
import { GrayIcon } from '../bulma_derived_components';
import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";
import { useState } from "react";
import ModalContainer from "@/components/common/ModalContainer";
import { useEffect, useCallback } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';
import { mutate } from 'swr';

const ShowStatsIcon = styled(GrayIcon)<{ $showStats: boolean }>`
    width: 2rem;
    height: 2rem;
    color: ${props => props.$showStats ? "#76bf96" : "#c6c6c6"};
    &:hover {
        color: #76bf96;
    }
`;

const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean)=>void }) => {
    return (
        <div onClick={() => setShowStats(!showStats)}>
            <ShowStatsIcon $showStats={showStats}>
                <i className="fas fa-lg fa-chart-bar"></i>
            </ShowStatsIcon>
        </div>
    )
}

export const PanelHeader = styled.div`
    display: flex;
    justify-content: space-between;
    background-color:'#DBE2F5'; 
    margin: 1rem;
    margin-bottom: 0;
    flex-grow: 0;
`;

export const PanelBody = styled.div`
    overflow-y: auto;
    flex-grow: 1;
    padding: 1rem;
`;

export const PanelContainer = styled.div`
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
`;


interface PlanPanelProps {
    setModalKey: (arg0: string) => void;
    modalKey: string;
    setModalObject: (arg0: DegreePlan | null) => void;
    setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
    activeDegreeplan: DegreePlan | undefined;
    degreeplans: DegreePlan[] | undefined;
    isLoading: boolean;
}

const PlanPanel = ({ setModalKey, modalKey, setModalObject, setActiveDegreeplanId, activeDegreeplan, degreeplans, isLoading } : PlanPanelProps) => {
    const { copy: copyDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
    const [showStats, setShowStats] = useState(true);

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
                    />
                    <ShowStatsButton showStats={showStats} setShowStats={setShowStats} />
                </PanelHeader>
                {/** map to semesters */}
                <PanelBody>
                    <Semesters activeDegreeplan={activeDegreeplan} showStats={showStats} />
                </PanelBody>
            </PanelContainer>
    );
}

export default PlanPanel;