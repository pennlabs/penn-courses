import { GrayIcon } from '../common/bulma_derived_components';
import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { DegreePlan } from "@/types";
import { useState } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';

export const PanelTopBarIcon = styled(GrayIcon)<{ $active: boolean }>`
    width: 2rem;
    height: 2rem;
    color: ${props => props.$active ? "#76bf96" : "#c6c6c6"};
    &:hover {
        color: #76bf96;
    }
`;

const ShowStatsButton = ({ showStats, setShowStats }: { showStats: boolean, setShowStats: (arg0: boolean)=>void }) => {
    return (
        <div onClick={() => setShowStats(!showStats)}>
            <PanelTopBarIcon $active={showStats}>
                <i className="fas fa-lg fa-chart-bar"></i>
            </PanelTopBarIcon>
        </div>
    )
}

export const EditButton = ({ editMode, setEditMode }: { editMode: boolean, setEditMode: (arg0: boolean)=>void }) => {
    return (
        <div onClick={() => setEditMode(!editMode)}>
            <PanelTopBarIcon $active={editMode}>
                <i className="fas fa-lg fa-edit"></i>
            </PanelTopBarIcon>
        </div>
    )
}

export const PanelHeader = styled.div`
    display: flex;
    justify-content: space-between;
    background-color: var(--primary-color);
    padding: 0.5rem 1rem;
    flex-grow: 0;
    font-size: 1.5rem;
    font-weight: 300;
`;

export const PanelBody = styled.div`
    padding: 10px;
    height: 100%;
    overflow-y: auto;
    flex-grow: 1;
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

const PlanPanel = ({ setModalKey, modalKey, setModalObject, setActiveDegreeplanId, activeDegreeplan, degreeplans } : PlanPanelProps) => {
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
                    />
                </PanelBody>
            </PanelContainer>
    );
}

export default PlanPanel;