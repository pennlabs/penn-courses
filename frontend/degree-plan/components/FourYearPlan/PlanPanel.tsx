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
    height: 100%;
`;

type ModalKey = "create" | "rename" | "remove" | null; // null is closed

const getModalTitle = (modalState: ModalKey) => {
    switch (modalState) {
        case "create":
            return "Create a new degree plan";
        case "rename":
            return "Rename degree plan";
        case "remove":
            return "Remove degree plan";
        default:
            return "";
    }
}

const ModalInteriorWrapper = styled.div<{ $row?: boolean }>`
    display: flex;
    flex-direction: ${props => props.$row ? "row" : "column"};
    align-items: center;
    padding: 1rem;
    gap: .5rem;
    text-align: center;
`;

const ModalInput = styled.input`
    background-color: #fff;
    color: black;
`;

const ModalButton = styled.button`
    background-color: rgb(98, 116, 241);
    border-radius: .25rem;
    padding: .25rem .5rem;
    color: white;
    border: none;
`;

interface ModalInteriorProps {
    modalKey: ModalKey;
    modalObject: DegreePlan | null;
    create: (name: string) => void;
    rename: (name: string, id: DegreePlan["id"]) => void;
    remove: (id: DegreePlan["id"]) => void;
    close: () => void;
}
const ModalInterior = ({ modalObject, modalKey, close, create, rename, remove }: ModalInteriorProps) => {
    const [name, setName] = useState<string>(modalObject?.name || "");

    if (modalKey === "create") {
        return (
            <ModalInteriorWrapper $row>
                <ModalInput type="text" placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
                <ModalButton onClick={
                    () => {
                        create(name);
                        close();
                    }
                }>
                    Create
                </ModalButton>
            </ModalInteriorWrapper>
        );
    }
    if (!modalKey || !modalObject) return <div></div>;

    switch (modalKey) {
        case "rename":
            return (
                <ModalInteriorWrapper>
                    <ModalInput type="text" placeholder="New name" value={name} onChange={e => setName(e.target.value)} />
                    <ModalButton onClick={() => {
                        rename(name, modalObject.id);
                        close();
                    }}>
                        Rename
                    </ModalButton>
                </ModalInteriorWrapper>
            );
        case "remove":
            return (
                <ModalInteriorWrapper>
                    <p>Are you sure you want to remove this degree plan?</p>
                    <ModalButton onClick={() => {
                        remove(modalObject.id)
                        close();
                    }}>Remove</ModalButton>
                </ModalInteriorWrapper>
            );
    }
}

interface PlanPanelProps {
    setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
    activeDegreeplan: DegreePlan | undefined;
    degreeplans: DegreePlan[] | undefined;
    isLoading: boolean;
}

const PlanPanel = ({ setActiveDegreeplanId, activeDegreeplan, degreeplans, isLoading } : PlanPanelProps) => {
    const { create: createDegreeplan, update: updateDegreeplan, remove: deleteDegreeplan, copy: copyDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');

    const [modalKey, setModalKey] = useState<ModalKey>(null);
    const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // stores the which degreeplan is being updated using the modal
    const [showStats, setShowStats] = useState(true);

    return (
        <>
            <PanelContainer>
                {modalKey && <ModalContainer
                        title={getModalTitle(modalKey)}
                        close={() => setModalKey(null)}
                        isBig
                        modalKey={modalKey}
                    >
                        <ModalInterior
                        modalObject={modalObject}
                        create={(name) => { 
                            createDegreeplan({ name: name })
                            .then((new_) => new_ && setActiveDegreeplanId(new_.id))
                        }} 
                        rename={(name, id) => void updateDegreeplan({ name }, id)}
                        remove={(id) => {
                            deleteDegreeplan(id)
                            mutate(
                                key => key.startsWith(`/api/degree/degreeplans/${id}`),
                                undefined,
                                { revalidate: false }
                            )
                        }}
                        />
                    </ModalContainer>
                    }
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
                                setModalKey("remove")
                                setModalObject(item)
                            },
                            rename: (item: DegreePlan) => {
                                setModalKey("rename")
                                setModalObject(item)
                            },
                            create: () => setModalKey("create")
                        }}              
                    />
                    <ShowStatsButton showStats={showStats} setShowStats={setShowStats} />
                </PanelHeader>
                {/** map to semesters */}
                <PanelBody>
                    <Semesters activeDegreeplan={activeDegreeplan} showStats={showStats} />
                </PanelBody>
            </PanelContainer>
        </>
    );
}

export default PlanPanel;