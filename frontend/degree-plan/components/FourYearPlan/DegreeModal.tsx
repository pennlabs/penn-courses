import styled from "@emotion/styled";
import type {
  DegreeListing,
  DegreePlan,
  Fulfillment,
  MajorOption,
  SchoolOption,
  Semester,
} from "@/types";
import React, { useState } from "react";
import { deleteFetcher, postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import useSWR, { useSWRConfig } from "swr";
import ModalContainer from "../common/ModalContainer";
import Select from "react-select";

export type ModalKey =
  | "plan-create"
  | "plan-rename"
  | "plan-remove"
  | "degree-add"
  | "degree-remove"
  | "semester-remove"
  | null; // null is closed

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
};

const ModalInteriorWrapper = styled.div<{ $row?: boolean }>`
  display: flex;
  flex-direction: ${(props) => (props.$row ? "row" : "column")};
  align-items: center;
  gap: 1.2rem;
  text-align: center;
`;

const ModalInput = styled.input`
  background-color: #fff;
  color: black;
  height: 32px;
`;

const ModalTextWrapper = styled.div`
  text-align: start;
  width: 100%;
`

const ModalText = styled.div`
  color: var(--modal-text-color);
  font-size: 0.87rem;
`

const ModalButton = styled.button`
  margin: 0px 0px 0px 0px;
  height: 32px;
  width: 5rem;
  background-color: var(--modal-button-color);
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  color: white;
  border: none;
`;

const ButtonRow = styled.div<{ $center?: boolean }>`
  display: flex;
  width: 100%;
  flex-direction: row;
  justify-content: ${(props) => (props.$center ? "center" : "flex-end")};
  gap: 0.5rem;
`

const CancelButton = styled.button`
  margin: 0px 0px 0px 0px;
  height: 29px;
  width: 4rem;
  background-color: transparent;
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  color: var(--modal-button-color);
  border: none;
`

const SelectList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: left;
  width: 100%;
`

const DegreeAddInterior = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
  padding: 1.2rem 2rem 280px;
`


interface RemoveDegreeProps {
  degreeplanId: number;
  degreeId: number;
}

interface RemoveSemesterProps {
  helper: () => void;
}

interface ModalInteriorProps {
  modalKey: ModalKey;
  modalObject: DegreePlan | null | RemoveSemesterProps | RemoveDegreeProps;
  setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
  close: () => void;
}
const ModalInterior = ({
  modalObject,
  modalKey,
  setActiveDegreeplanId,
  close,
}: ModalInteriorProps) => {
  const {
    create: createDegreeplan,
    update: updateDegreeplan,
    remove: deleteDegreeplan,
  } = useSWRCrud<DegreePlan>("/api/degree/degreeplans");
  const { mutate } = useSWRConfig();

  const create_degreeplan = (name: string) => {
    createDegreeplan({ name }).then(
      (new_) => new_ && setActiveDegreeplanId(new_.id)
    );
  };
  const [school, setSchool] = useState<SchoolOption>();
  const [major, setMajor] = useState<MajorOption>();

  const [name, setName] = useState<string>(modalObject?.name || "");
  // const [degreeId, setDegreeId] = useState<number | null>(null);

  const { data: degrees, isLoading: isLoadingDegrees } =
    useSWR<DegreeListing[]>(`/api/degree/degrees`);

  const defaultSchools = ["BSE", "BA", "BAS", "BS"];

  const schoolOptions = defaultSchools.map((d) => ({
    value: d,
    label: d,
  }));
  // console.log('schooOptions', schoolOptions);

  /** Create label for major listings */
  const createMajorLabel = (degree: DegreeListing) => {
    const concentration =
      degree.concentration && degree.concentration !== "NONE"
        ? ` - ${degree.concentration}`
        : "";
    return `${degree.major}${concentration}`;
  };

  const getMajorOptions = React.useCallback(() => {
    /** Filter major options based on selected schools/degrees */
    const majorOptions =
      degrees
        ?.filter((d) => school?.value === d.degree)
        .map((degree) => ({
          value: degree,
          label: createMajorLabel(degree),
        })) || [];
    return majorOptions;
  }, [school]);

  if (!modalKey || !modalObject) return <div></div>;

  const add_degree = async (degreeplanId, degreeId) => {
    const updated = await postFetcher(
      `/api/degree/degreeplans/${degreeplanId}/degrees`,
      { degree_ids: [degreeId] }
    ); // add degree
    mutate(`/api/degree/degreeplans/${degreeplanId}`, updated, {
      populateCache: true,
      revalidate: true,
    }); // use updated degree plan returned
    mutate(
      (key) =>
        key &&
        key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`)
    ); // refetch the fulfillments
  };
  const remove_degree = async (degreeplanId, degreeId) => {
    const updated = await deleteFetcher(
      `/api/degree/degreeplans/${degreeplanId}/degrees`,
      { degree_ids: [degreeId] }
    ); // remove degree
    mutate(`/api/degree/degreeplans/${degreeplanId}`, updated, {
      populateCache: true,
      revalidate: false,
    }); // use updated degree plan returned
    mutate(
      (key) =>
        key &&
        key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`)
    ); // refetch the fulfillments
  };

  switch (modalKey) {
    case "plan-create":
      return (
        <ModalInteriorWrapper $row={false}>
          <ModalInput
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <ButtonRow>
            <CancelButton onClick={close}>
              Cancel
            </CancelButton>
            <ModalButton
              onClick={() => {
                create_degreeplan(name);
                close();
              }}
            >
              Create
            </ModalButton>
          </ButtonRow>
        </ModalInteriorWrapper>
      );
    case "plan-rename":
      return (
        <ModalInteriorWrapper>
          <ModalInput
            type="text"
            placeholder="New name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          {/* <ButtonRow> */}
          <ModalButton
            onClick={() => {
              updateDegreeplan({ name }, modalObject.id)
              close();
            }}
          >
            Rename
          </ModalButton>
          {/* </ButtonRow> */}
        </ModalInteriorWrapper>
      );
    case "plan-remove":
      return (
        <ModalInteriorWrapper>
            <ModalTextWrapper>
              <ModalText>Are you sure you want to remove this degree plan?</ModalText>
            </ModalTextWrapper>
            <ButtonRow $center={true}>
              <ModalButton
                onClick={() => {
                  deleteDegreeplan(modalObject.id);
                  close();
                }}
              >
                Remove
              </ModalButton>
            </ButtonRow>
        </ModalInteriorWrapper>
      );
    case "degree-add":
      return (
        <ModalInteriorWrapper>
          <DegreeAddInterior>
            <SelectList>
              <Select
                options={schoolOptions}
                value={school}
                onChange={(selectedOption) => setSchool(selectedOption)}
                isClearable
                placeholder="Select School or Program"
                isLoading={isLoadingDegrees}
              />
              <Select
                options={getMajorOptions()}
                value={major}
                onChange={(selectedOption) => setMajor(selectedOption)}
                isClearable
                placeholder={
                  school ? "Major - Concentration" : "Please Select Program First"
                }
                isLoading={isLoadingDegrees}
              />
            </SelectList>
            <ButtonRow $center={true}>
              <ModalButton
                onClick={() => {
                  if (!major?.value.id) return;
                  add_degree(modalObject.id, major?.value.id);
                  close();
                }}
              >
                Add
              </ModalButton>
            </ButtonRow>
          </DegreeAddInterior>
        </ModalInteriorWrapper>
      );
    case "degree-remove":
      return (
        <ModalInteriorWrapper>
          <ModalTextWrapper>
              <ModalText>Are you sure you want to remove this degree? All of your planning for this degree will be lost</ModalText>
            </ModalTextWrapper>
          <ModalButton
            onClick={() => {
              remove_degree(modalObject.degreeplanId, modalObject.degreeId);
              close();
            }}
          >
            Remove
          </ModalButton>
        </ModalInteriorWrapper>
      );
    case "semester-remove":
      return (
        <ModalInteriorWrapper>
          <p>
            Are you sure you want to remove this semester? All of your planning
            for this semester will be lost
          </p>
          <ModalButton
            onClick={() => {
              modalObject.helper();
              close();
            }}
          >
            Remove
          </ModalButton>
        </ModalInteriorWrapper>
      );
  }
  return <div></div>;
};

interface DegreeModalProps {
  setModalKey: (arg0: ModalKey) => void;
  modalKey: ModalKey;
  modalObject: DegreePlan | null;
  setActiveDegreeplanId: (arg0: DegreePlan["id"]) => void;
}
const DegreeModal = ({
  setModalKey,
  modalKey,
  modalObject,
  setActiveDegreeplanId,
}: DegreeModalProps) => (
  <ModalContainer
    title={getModalTitle(modalKey)}
    close={() => setModalKey(null)}
    modalKey={modalKey}
  >
    <ModalInterior
      modalObject={modalObject}
      setActiveDegreeplanId={setActiveDegreeplanId}
      close={() => setModalKey(null)}
    />
  </ModalContainer>
);

export default DegreeModal;
