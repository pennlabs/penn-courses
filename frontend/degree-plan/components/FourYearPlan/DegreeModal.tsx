import styled from "@emotion/styled";
import type { DegreeListing, DegreePlan, Fulfillment, MajorOption, SchoolOption, Semester } from "@/types";
import React, { useState } from "react";
import { deleteFetcher, postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import useSWR, { useSWRConfig } from "swr";
import ModalContainer from "../common/ModalContainer";
import Select from "react-select";

export type ModalKey = "plan-create" | "plan-rename" | "plan-remove" | "degree-add" | "degree-remove" | "semester-remove" | null; // null is closed

const getModalTitle = (modalState: ModalKey) => {
    switch (modalState) {
        case "plan-create":
            return "Create a new degree plan";
        case "plan-rename":
            return "Rename degree plan";
        case "plan-remove":
            return "Remove degree plan";
        case "degree-add":
            return "Add degree";
        case "degree-remove":
            return "Remove degree";
        case "semester-remove": 
            return "Remove semester";
        case null:
            return "";
        default:
            throw Error("Invalid modal key: ");
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
    modalObject: DegreePlan | null | {helper: () => void};
    setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
    close: () => void;
}
const ModalInterior = ({ modalObject, modalKey, setActiveDegreeplanId, close }: ModalInteriorProps) => {
    const { create: createDegreeplan, update: updateDegreeplan, remove: deleteDegreeplan, copy: copyDegreeplan } = useSWRCrud<DegreePlan>('/api/degree/degreeplans');
    const { mutate } = useSWRConfig();

    const create_degreeplan = (name: string) => { 
        createDegreeplan({ name: name })
        .then((new_) => new_ && setActiveDegreeplanId(new_.id))
    }
    const [school, setSchool] = useState<SchoolOption>();
    const [major, setMajor] = useState<MajorOption>();

    const [name, setName] = useState<string>(modalObject?.name || "");
    // const [degreeId, setDegreeId] = useState<number | null>(null);

    const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
        DegreeListing[]
    >(`/api/degree/degrees`);

    const defaultSchools = ['BSE', 'BA', 'BAS', 'BS'];

    const schoolOptions =
        defaultSchools.map((d) => ({
        value: d,
        label: d
        }))
    // console.log('schooOptions', schoolOptions);

    /** Create label for major listings */
    const createMajorLabel = (degree: DegreeListing) => {
        const concentration = 
        degree.concentration && degree.concentration !== 'NONE' 
            ? ` - ${degree.concentration}`
            : '';
        return `${degree.major}${concentration}`;
    }

    const getMajorOptions = React.useCallback(() => {
        /** Filter major options based on selected schools/degrees */
        const majorOptions = degrees
        ?.filter(d => school?.value === d.degree)
        .map((degree) => ({ value: degree, label: createMajorLabel(degree)})) 
        || [];
        return majorOptions;
    }, [school]);


    if (modalKey === "plan-create") {
        return (
            <ModalInteriorWrapper $row>
                <ModalInput type="text" placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
                <ModalButton onClick={
                    () => {
                        create_degreeplan(name);
                        close();
                    }
                }>
                    Create
                </ModalButton>
            </ModalInteriorWrapper>
        );
    }
    if (!modalKey || !modalObject) return <div></div>;
    
    const rename_degreeplan = (name: string, id: DegreePlan["id"]) => void updateDegreeplan({ name }, id)
    const remove_degreeplan = (id) => {
        deleteDegreeplan(id)
        mutate(
            key => key.startsWith(`/api/degree/degreeplans/${id}`),
            undefined,
            { revalidate: false }
        )
    }
    const add_degree = (degreeplanId, degreeId) => {
        const updated = postFetcher(`/api/degree/degreeplans/${degreeplanId}/degrees`, { degree_ids: [degreeId] }) // add degree
        mutate(`api/degree/degreeplans/${degreeplanId}`, updated, { populateCache: true, revalidate: false }) // use updated degree plan returned
        mutate(key => key && key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`)) // refetch the fulfillments   
    }
    const remove_degree = (degreeplanId, degreeId) => {
        const updated = deleteFetcher(`/api/degree/degreeplans/${degreeplanId}/degrees`, { degree_ids: [degreeId] }) // remove degree
        mutate(`api/degree/degreeplans/${degreeplanId}`, updated, { populateCache: true, revalidate: false }) // use updated degree plan returned
        mutate(key => key && key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`)) // refetch the fulfillments   
    }

    const remove_semester = (degreeplanId: number, fulfillments:Fulfillment[]) => {
        // console.log('new fulfillments: ', fulfillments.map(f => f.full_code));
        // const updated = deleteFetcher(`/api/degree/degreeplans/${degreeplanId}/fulfillments`, {full_code: 'PHYS-3351'}) 
        // mutate(`/api/degree/degreeplans/${degreeplanId}/fulfillments`, updated, { populateCache: true, revalidate: false }) // use updated degree plan returned
        // mutate(key => key && key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`))// refetch the fulfillments 
    }

    switch (modalKey) {
        case "plan-rename":
            return (
                <ModalInteriorWrapper>
                    <ModalInput type="text" placeholder="New name" value={name} onChange={e => setName(e.target.value)} />
                    <ModalButton onClick={() => {
                        rename_degreeplan(name, modalObject.id);
                        close();
                    }}>
                        Rename
                    </ModalButton>
                </ModalInteriorWrapper>
            );
        case "plan-remove":
            return (
                <ModalInteriorWrapper>
                    <p>Are you sure you want to remove this degree plan?</p>
                    <ModalButton onClick={() => {
                        remove_degreeplan(modalObject.id)
                        close();
                    }}>Remove</ModalButton>
                </ModalInteriorWrapper>
            );
        case "degree-add":
            return (
                <ModalInteriorWrapper>
                    <div style={{display: 'flex', flexDirection: 'row'}}>
                        <Select
                            options={schoolOptions}
                            value={school}
                            onChange={(selectedOption) => setSchool(selectedOption)}
                            isClearable
                            placeholder="Select School or Program"
                            // styles={customSelectStylesRight}
                            isLoading={isLoadingDegrees}
                            />
                        <Select
                            options={getMajorOptions()}
                            value={major}
                            onChange={(selectedOption) => setMajor(selectedOption)}
                            isClearable
                            placeholder={school ? "Major - Concentration" : "Please Select Program First"}
                            // styles={customSelectStylesRight}
                            isLoading={isLoadingDegrees}
                            />
                    </div>
                    <ModalButton onClick={() => {
                        if (!major?.value.id) return;
                        add_degree(modalObject.id, major?.value.id);
                        close();
                    }}>Add</ModalButton>
                </ModalInteriorWrapper>
            );
        case "degree-remove":
            return (
                <ModalInteriorWrapper>
                    <p>Are you sure you want to remove this degree? All of your planning for this degree will be lost</p>
                    <ModalButton onClick={() => {
                        remove_degree(modalObject.id, modalObject.id)
                        close();
                    }}>Remove</ModalButton>
                </ModalInteriorWrapper>
            );
        case "semester-remove":
            return (
                <ModalInteriorWrapper>
                    <p>Are you sure you want to remove this semester? All of your planning for this semester will be lost</p>
                    <ModalButton onClick={() => {
                        modalObject.helper();
                        // remove_semester(modalObject.degreeplanId, modalObject.fulfillments);
                        close();
                    }}>Remove</ModalButton>
                </ModalInteriorWrapper>
            );
    }
    return <div></div>;
}

interface DegreeModalProps {
    setModalKey: (arg0: ModalKey) => void;
    modalKey: ModalKey;
    modalObject: DegreePlan | null;
    setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
}
const DegreeModal = ({ setModalKey, modalKey, modalObject, setActiveDegreeplanId, }: DegreeModalProps) => (
    <ModalContainer
    title={getModalTitle(modalKey)}
    close={() => setModalKey(null)}
    isBig
    modalKey={modalKey}
    >
        <ModalInterior modalObject={modalObject} setActiveDegreeplanId={setActiveDegreeplanId} />
    </ModalContainer>
)

export default DegreeModal;