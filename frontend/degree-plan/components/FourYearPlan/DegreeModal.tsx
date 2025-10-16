import styled from "@emotion/styled";
import type {
  Degree,
  DegreeListing,
  DegreePlan,
  Fulfillment,
  MajorOption,
  SchoolOption,
  Semester,
} from "@/types";
import React, { useState } from "react";
import {
  deleteFetcher,
  getFetcher,
  postFetcher,
  useSWRCrud,
} from "@/hooks/swrcrud";
import useSWR, { useSWRConfig } from "swr";
import ModalContainer from "../common/ModalContainer";
import Select from "react-select";
import { schoolOptions } from "./OnboardingPage";

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

const SelectList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: left;
  width: 100%;
`;

const DegreeAddInterior = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
  width: 100%;
  padding: 1.2rem 2rem;
`;

/** Create label for major listings */
export const createMajorLabel = (degree: DegreeListing) => {
  const concentration =
    degree.concentration && degree.concentration !== "NONE"
      ? ` - ${degree.concentration_name}`
      : "";
  return `${degree.major_name}${concentration} (${degree.year})`;
};

interface RemoveDegreeProps {
  degreeplanId: number;
  degreeId: number;
}

interface RemoveSemesterProps {
  helper: () => void;
}

interface ModalInteriorProps {
  modalKey: ModalKey;
  modalObject: DegreePlan | null | RemoveSemesterProps | RemoveDegreeProps | Degree;
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
  modalRef
}: ModalInteriorProps) => {
  const {
    create: createDegreeplan,
    update: updateDegreeplan,
    remove: deleteDegreeplan,
  } = useSWRCrud<DegreePlan>("/api/degree/degreeplans");

  const { mutate } = useSWRConfig();

  // Need to add modalRef
  const [modalRefCurrent, setModalRefCurrent] = useState<HTMLSelectElement | null>(null);

  React.useEffect(() => {
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

  const [school, setSchool] = useState<SchoolOption>();
  const [major, setMajor] = useState<MajorOption>();
  const [name, setName] = useState<string>("");

  const { data: degrees, isLoading: isLoadingDegrees } =
    useSWR<DegreeListing[]>(`/api/degree/degrees`);

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

  if (!modalKey && !modalObject) return <div></div>;

  const add_degree = async (degreeplanId: number, degreeId: number) => {
    // const { mutate } = useSWR(`/api/degree/degreeplans/${degreeplanId}/degrees`, getFetcher);
    const updated = await postFetcher(
      `/api/degree/degreeplans/${degreeplanId}/degrees`,
      { degree_ids: [degreeId] }
    );
    await mutate(`/api/degree/degreeplans/${degreeplanId}`); // use updated degree plan returned
    await mutate(`/api/degree/degreeplans/${degreeplanId}/fulfillments`);
  };

  const remove_degree = async (degreeplanId: number, degreeId: number) => {
    await deleteFetcher(`/api/degree/degreeplans/${degreeplanId}/degrees`, {
      
      degree_ids: [degreeId],
    }); // remove degree
    await mutate(`/api/degree/degreeplans/${degreeplanId}`); // use updated degree plan returned
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
          {/* <ButtonRow> */}
          <ModalButton
            onClick={() => {
              updateDegreeplan({ name }, (modalObject as DegreePlan).id);
              
              

              if ((modalObject as DegreePlan).id == activeDegreePlan?.id) {
                let newNameDegPlan = (modalObject as DegreePlan);
                newNameDegPlan.name = name;
                setActiveDegreeplan(newNameDegPlan);
              }
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
    case "degree-add":
      return (
        <ModalInteriorWrapper>
          <DegreeAddInterior>
            <SelectList>
              <Select
                options={schoolOptions}
                value={school}
                onChange={(selectedOption) => setSchool(selectedOption || undefined)}
                isClearable
                placeholder="Select School or Program"
                isLoading={false}
                styles={{ menuPortal: base => ({ ...base, zIndex: 999 }) }}
                menuPortalTarget={modalRefCurrent}

              />
              <Select
                options={getMajorOptions()}
                value={major}
                onChange={(selectedOption) => setMajor(selectedOption || undefined)}
                styles={{ menuPortal: base => ({ ...base, zIndex: 999 }) }}
                menuPortalTarget={modalRefCurrent}
                isClearable
                isDisabled={!school}
                placeholder={
                  isLoadingDegrees
                    ? "loading programs..."
                    : "Major - Concentration (Starting Year)"
                }
                isLoading={isLoadingDegrees}
              />
            </SelectList>
            <ButtonRow $center={true}>
              <ModalButton
                onClick={() => {
                  if (!major?.value.id) return;
                  add_degree((modalObject as Degree).id, major?.value.id);
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
            <ModalText>
              Are you sure you want to remove this degree? All of your planning
              for this degree will be lost.
            </ModalText>
          </ModalTextWrapper>
          <ModalButton
            onClick={() => {
              remove_degree((modalObject as RemoveDegreeProps).degreeplanId, (modalObject as RemoveDegreeProps).degreeId);
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
          <ModalTextWrapper>
            <ModalText>
              Are you sure you want to remove this semester? All of your
              planning for this semester will be lost.
            </ModalText>
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
