import update from 'immutability-helper'
import _, { create, get } from "lodash";
import { GrayIcon } from '../bulma_derived_components';
import SelectListDropdown from "./SelectListDropdown";
import Semesters from "./Semesters";
import styled from "@emotion/styled";
import type { Degree, DegreePlan } from "@/types";
import { useState } from "react";
import ModalContainer from "@/components/common/ModalContainer";
import { useEffect, useCallback } from "react";
import { useSWRCrud } from '@/hooks/swrcrud';

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

const PlanPanelHeader = styled.div`
    display: flex;
    justify-content: space-between;
    background-color:'#DBE2F5'; 
    margin: 1rem;
    margin-bottom: 0;
    flex-grow: 0;
`;

const OverflowSemesters = styled(Semesters)`
    overflow-y: scroll;
    flex-grow: 1;
    padding: 1rem;
`;

const PlanPanelContainer = styled.div`
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
                    <ModalButton onClick={() => remove(modalObject.id)}>Remove</ModalButton>
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
    const { create: createDegreeplan, update: updateDegreeplan, remove: deleteDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans/');

    const [modalKey, setModalKey] = useState<ModalKey>(null);
    const [modalObject, setModalObject] = useState<DegreePlan | null>(null); // object being updated using the modal
    const defaultSemester1 = {id: 1, name: 'Semester 1', courses:[], cu: 0};
    const defaultSemester2 = {id: 2, name: 'Semester 2', courses:[], cu: 0};
    const defaultSemester3 = {id: 3, name: 'Semester 3', courses:[], cu: 0};
    const defaultSemester4 = {id: 4, name: 'Semester 4', courses:[], cu: 0};
    const defaultSemester5 = {id: 5, name: 'Semester 5', courses:[], cu: 0};
    const defaultSemester6 = {id: 6, name: 'Semester 6', courses:[], cu: 0};
    const defaultSemester7 = {id: 7, name: 'Semester 7', courses:[], cu: 0};

    const [semesters, setSemesters] = useState([defaultSemester1, defaultSemester2, defaultSemester3, defaultSemester4, defaultSemester5, defaultSemester6, defaultSemester7]);
    const [showStats, setShowStats] = useState(true);

    useEffect(() => {
        setSemesters(semesters);
    }, [semesters])

    const addCourse = (toIndex: number, course: any, fromIndex:number) => {
        if (fromIndex === toIndex) return;
        // when from index is -1, the course is dragged from outside of the planning panel
        if (fromIndex !== -1) removeCourseFromSem(fromIndex, course); // remove from originally planned semester
        addCourseToSem(toIndex, course); // add to newly planned semester
    }

    const addCourseToSem = useCallback((toIndex: number, course: any) => {
        setSemesters((sems) =>
            update(sems, {
                [toIndex]: {
                    courses: {
                        /** filter the array to avoid adding the same course twice */
                        $apply: (courses: any) => courses.filter((c: any) => c.id != course.id),
                        $push: [course]
                    }
                }
            })
        )
    }, []);

    const removeCourseFromSem = (index: number, course: any) => {
        setSemesters((sems) =>
            update(sems, {
                [index]: {
                    courses: {
                        $apply: (courses: any) => courses.filter((c: any) => c.id != course.id),
                    }
                }
            })
        )
    };

    return (
        <>
            <PlanPanelContainer>
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
                        remove={(id) => void deleteDegreeplan(id)}
                        />
                    </ModalContainer>
                    }
                <PlanPanelHeader>
                    <SelectListDropdown
                        itemType="degree plan" 
                        active={activeDegreeplan}
                        getItemName={(item: DegreePlan) => item.name}
                        allItems={degreeplans || []} 
                        selectItem={(id: DegreePlan["id"]) => setActiveDegreeplanId(id)}
                        mutators={{
                            copy: (item: DegreePlan) => {
                                // TODO: something like
                                // copyDegreeplan(item.id)
                                // .then((copied) => copied && setActiveDegreeplanId(copied.id))
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
                </PlanPanelHeader>
                {/** map to semesters */}
                <OverflowSemesters semesters={semesters} setSemesters={setSemesters} showStats={showStats} addCourse={addCourse}/>
            </PlanPanelContainer>
        </>
    );
}

export default PlanPanel;