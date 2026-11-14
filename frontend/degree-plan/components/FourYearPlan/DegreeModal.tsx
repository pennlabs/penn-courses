import styled from "@emotion/styled";
import type { DegreeListing, DegreePlan } from "@/types";
import React, { useState, useEffect } from "react";
import { deleteFetcher, postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { useSWRConfig } from "swr";
import { programYear } from "@/utils/programs";
import ModalContainer from "../common/ModalContainer";

export type ModalKey =
  | "plan-create"
  | "plan-rename"
  | "plan-remove"
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
    case "semester-remove":
      return "Remove semester";
    case null:
      return "";
    default:
      throw Error("Invalid modal key: ");
  }
};

const DELETE_CONFIRMATION_MESSAGE = (subject: string) =>
  `Are you sure you want to remove this ${subject}? All of your planning for this ${subject} will be lost.`;

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
`;

const ModalText = styled.div`
  color: var(--modal-text-color);
  font-size: 0.87rem;
`;

const ModalButton = styled.button`
  margin: 0px 0px 0px 0px;
  height: 32px;
  width: 5rem;
  background-color: var(--modal-button-color);
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  color: white;
  border: none;
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const ButtonRow = styled.div<{ $center?: boolean }>`
  display: flex;
  width: 100%;
  flex-direction: row;
  justify-content: ${(props) => (props.$center ? "center" : "flex-end")};
  gap: 0.5rem;
`;

const CancelButton = styled.button`
  margin: 0px 0px 0px 0px;
  height: 29px;
  width: 4rem;
  background-color: transparent;
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  color: var(--modal-button-color);
  border: none;
`;

/** Create label for major listings */
export const createMajorLabel = (degree: DegreeListing) => {
  const concentration =
    degree.concentration && degree.concentration !== "NONE"
      ? ` - ${degree.concentration_name}`
      : "";
  const year = programYear(degree.year);
  return `${degree.major_name}${concentration}${year ? ` (${year})` : ""}`;
};

interface RemoveSemesterProps {
  helper: () => void;
}

interface ModalInteriorProps {
  modalKey: ModalKey;
  modalObject:
    | DegreePlan
    | null
    | RemoveSemesterProps;
  activeDegreePlan: DegreePlan | null;
  setActiveDegreeplan: (arg0: DegreePlan | null) => void;
  close: () => void;
  modalRef: React.RefObject<HTMLSelectElement | null>;
}
const ModalInterior = ({
  modalObject,
  modalKey,
  activeDegreePlan,
  setActiveDegreeplan,
  close,
  modalRef,
}: ModalInteriorProps) => {
  const {
    create: createDegreeplan,
    update: updateDegreeplan,
    remove: deleteDegreeplan,
  } = useSWRCrud<DegreePlan>("/api/degree/degreeplans");

  const { mutate } = useSWRConfig();

  const [
    modalRefCurrent,
    setModalRefCurrent,
  ] = useState<HTMLSelectElement | null>(null);

  useEffect(() => {
    setModalRefCurrent(modalRef.current);
  }, [modalRef]);

  const add_degreeplan = async (name: string) => {
    const _new = await postFetcher("/api/degree/degreeplans", { name: name });
    await mutate("/api/degree/degreeplans"); // use updated degree plan returned
    setActiveDegreeplan(_new);
  };

  const delete_degreeplan = async (id: number) => {
    await deleteFetcher(`/api/degree/degreeplans/${id}`);
    await mutate("/api/degree/degreeplans"); // use updated degree plan returned
  };

  const [name, setName] = useState<string>("");

  if (!modalKey && !modalObject) return <div></div>;

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
            <CancelButton onClick={close}>Cancel</CancelButton>
            <ModalButton
              onClick={() => {
                add_degreeplan(name);

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
          <ModalButton
            onClick={() => {
              if (
                modalObject &&
                "id" in modalObject &&
                "name" in modalObject
              ) {
                updateDegreeplan({ name }, modalObject.id);
                if (modalObject.id == activeDegreePlan?.id) {
                  let newNameDegPlan = modalObject;
                  newNameDegPlan.name = name;
                  setActiveDegreeplan(newNameDegPlan);
                }
              }
              close();
            }}
          >
            Rename
          </ModalButton>
        </ModalInteriorWrapper>
      );
    case "plan-remove":
      return (
        <ModalInteriorWrapper>
          <ModalTextWrapper>
            <ModalText>
              Are you sure you want to remove this degree plan?
            </ModalText>
          </ModalTextWrapper>
          <ButtonRow $center={true}>
            <ModalButton
              onClick={() => {
                // TODO: these are not great type casts
                delete_degreeplan((modalObject as DegreePlan).id);
                close();
              }}
            >
              Remove
            </ModalButton>
          </ButtonRow>
        </ModalInteriorWrapper>
      );
    case "semester-remove":
      return (
        <ModalInteriorWrapper>
          <ModalTextWrapper>
            <ModalText>{DELETE_CONFIRMATION_MESSAGE("semester")}</ModalText>
          </ModalTextWrapper>
          <ModalButton
            onClick={() => {
              (modalObject as RemoveSemesterProps).helper();
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
  activeDegreePlan: DegreePlan | null;
  setActiveDegreeplan: (arg0: DegreePlan | null) => void;
}
const DegreeModal = ({
  setModalKey,
  modalKey,
  modalObject,
  activeDegreePlan,
  setActiveDegreeplan,
}: DegreeModalProps) => (
  <ModalContainer
    title={getModalTitle(modalKey)}
    close={() => setModalKey(null)}
    modalKey={modalKey}
  >
    {/*
    // @ts-ignore */}
    <ModalInterior
      modalObject={modalObject}
      activeDegreePlan={activeDegreePlan}
      setActiveDegreeplan={setActiveDegreeplan}
      close={() => setModalKey(null)}
    />
  </ModalContainer>
);

export default DegreeModal;
