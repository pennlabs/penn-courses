import styled from "@emotion/styled";
import type {
  Degree,
  DegreeListing,
  DegreePlan,
  DualProgram,
  Major,
  MajorOption,
  SchoolOption,
} from "@/types";
import React, { useState, useEffect } from "react";
import { deleteFetcher, postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import useSWR, { useSWRConfig } from "swr";
import ModalContainer from "../common/ModalContainer";
import Select from "react-select";
import { schoolOptions } from "@/components/OnboardingPanels/SharedComponents";

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
  font-size: var(--type-body);
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
  relation?: "degrees" | "majors" | "minors" | "dual";
}

interface RemoveSemesterProps {
  helper: () => void;
}

interface ModalInteriorProps {
  modalKey: ModalKey;
  modalObject:
    | DegreePlan
    | null
    | RemoveSemesterProps
    | RemoveDegreeProps
    | Degree;
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

  const [school, setSchool] = useState<SchoolOption>();
  const [major, setMajor] = useState<MajorOption>();
  const [name, setName] = useState<string>("");
  const [addMode, setAddMode] = useState<"degree" | "major" | "dual">("degree");
  const [secondMajor, setSecondMajor] = useState<Major | null>(null);
  const [dualChoice, setDualChoice] = useState<DualProgram | null>(null);
  const [dualLeft, setDualLeft] = useState<DegreeListing | null>(null);
  const [dualRight, setDualRight] = useState<DegreeListing | null>(null);

  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);
  const { data: standaloneMajors } = useSWR<Major[]>(`/api/degree/majors`);
  const { data: dualPrograms } = useSWR<DualProgram[]>(`/api/degree/dual-programs`);

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

  const [isAddingDegree, setIsAddingDegree] = useState(false);
  const add_degree = async (degreeplanId: number, degreeId: number) => {
    setIsAddingDegree(true);
    try {
      const updated = await postFetcher(
        `/api/degree/degreeplans/${degreeplanId}/degrees`,
        { degree_ids: [degreeId] }
      );
      await mutate(`/api/degree/degreeplans/${degreeplanId}`); // use updated degree plan returned
      await mutate(`/api/degree/degreeplans/${degreeplanId}/fulfillments`);
      await mutate(`/api/degree/degreeplans/${degreeplanId}/summary`);
    } catch (error) {
      console.error(error);
    } finally {
      setIsAddingDegree(false);
    }
  };

  const remove_degree = async (
    degreeplanId: number,
    degreeId: number,
    relation: "degrees" | "majors" | "minors" | "dual" = "degrees"
  ) => {
    // degrees -> degree_ids, majors -> major_ids, minors -> minor_ids
    const idsField = `${relation.slice(0, -1)}_ids`;
    const endpoint =
      relation === "dual"
        ? `/api/degree/degreeplans/${degreeplanId}/dual-program`
        : `/api/degree/degreeplans/${degreeplanId}/${relation}`;
    if (relation === "dual") {
      await deleteFetcher(endpoint);
    } else {
      await deleteFetcher(endpoint, { [idsField]: [degreeId] });
    }
    await mutate(`/api/degree/degreeplans/${degreeplanId}`);
    await mutate(`/api/degree/degreeplans/${degreeplanId}/fulfillments`);
    await mutate(`/api/degree/degreeplans/${degreeplanId}/summary`);
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
    case "degree-add":
      return (
        <ModalInteriorWrapper>
          <DegreeAddInterior>
            <SelectList>
              <Select
                options={[
                  { value: "degree" as const, label: "Add a degree" },
                  { value: "major" as const, label: "Add a second major" },
                  { value: "dual" as const, label: "Set a dual-degree program" },
                ]}
                value={{
                  value: addMode,
                  label:
                    addMode === "major"
                      ? "Add a second major"
                      : addMode === "dual"
                      ? "Set a dual-degree program"
                      : "Add a degree",
                }}
                onChange={(selected) => selected && setAddMode(selected.value)}
                styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
                menuPortalTarget={modalRefCurrent}
              />
              {addMode === "major" && (
                <Select
                  options={(standaloneMajors ?? []).map((item) => ({
                    value: item,
                    label: `${item.name ?? item.code} (${item.year})`,
                  }))}
                  onChange={(selected) => setSecondMajor(selected?.value ?? null)}
                  placeholder="Second major"
                  styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
                  menuPortalTarget={modalRefCurrent}
                />
              )}
              {addMode === "dual" && (
                <>
                  <Select
                    options={(dualPrograms ?? []).map((program) => ({
                      value: program,
                      label: program.name,
                    }))}
                    onChange={(selected) => {
                      setDualChoice(selected?.value ?? null);
                      setDualLeft(null);
                      setDualRight(null);
                    }}
                    placeholder="M&T, Huntsman, LSM, VIPER"
                    styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
                    menuPortalTarget={modalRefCurrent}
                  />
                  {dualChoice && (
                    <>
                      <Select
                        options={(degrees ?? [])
                          .filter(
                            (degree) =>
                              dualChoice.left_programs.includes(degree.program) &&
                              (dualChoice.left_allowed_majors.length === 0 ||
                                dualChoice.left_allowed_majors.includes(degree.major))
                          )
                          .map((degree) => ({
                            value: degree,
                            label: `${degree.major_name || degree.major} (${degree.year})`,
                          }))}
                        onChange={(selected) => setDualLeft(selected?.value ?? null)}
                        placeholder="First degree"
                        styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
                        menuPortalTarget={modalRefCurrent}
                      />
                      <Select
                        options={(degrees ?? [])
                          .filter(
                            (degree) =>
                              dualChoice.right_programs.includes(degree.program) &&
                              (dualChoice.right_allowed_majors.length === 0 ||
                                dualChoice.right_allowed_majors.includes(degree.major))
                          )
                          .map((degree) => ({
                            value: degree,
                            label: `${degree.major_name || degree.major} (${degree.year})`,
                          }))}
                        onChange={(selected) => setDualRight(selected?.value ?? null)}
                        placeholder="Second degree"
                        styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
                        menuPortalTarget={modalRefCurrent}
                      />
                    </>
                  )}
                </>
              )}
              {addMode === "degree" && (
              <>
              <Select
                options={schoolOptions}
                value={school}
                onChange={(selectedOption) =>
                  setSchool(selectedOption || undefined)
                }
                isClearable
                placeholder="Select School or Program"
                isLoading={false}
                styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
                menuPortalTarget={modalRefCurrent}
              />
              <Select
                options={getMajorOptions()}
                value={major}
                onChange={(selectedOption) =>
                  setMajor(selectedOption || undefined)
                }
                styles={{ menuPortal: (base) => ({ ...base, zIndex: 999 }) }}
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
              </>
              )}
            </SelectList>
            <ButtonRow $center={true}>
              <ModalButton
                disabled={isAddingDegree}
                onClick={async () => {
                  const planId = (modalObject as DegreePlan).id;
                  if (addMode === "major" && secondMajor) {
                    await postFetcher(`/api/degree/degreeplans/${planId}/majors`, {
                      major_ids: [secondMajor.id],
                    });
                    await mutate(`/api/degree/degreeplans/${planId}`);
                    await mutate(`/api/degree/degreeplans/${planId}/fulfillments`);
                    await mutate(`/api/degree/degreeplans/${planId}/summary`);
                  } else if (addMode === "dual" && dualChoice && dualLeft && dualRight) {
                    await postFetcher(`/api/degree/degreeplans/${planId}/dual-program`, {
                      code: dualChoice.code,
                      left_id: dualLeft.id,
                      right_id: dualRight.id,
                    });
                    await mutate(`/api/degree/degreeplans/${planId}`);
                    await mutate(`/api/degree/degreeplans/${planId}/fulfillments`);
                    await mutate(`/api/degree/degreeplans/${planId}/summary`);
                  } else if (major?.value.id) {
                    await add_degree(planId, major.value.id);
                  }
                  close();
                }}
              >
                {isAddingDegree ? "Adding..." : "Add"}
              </ModalButton>
            </ButtonRow>
          </DegreeAddInterior>
        </ModalInteriorWrapper>
      );
    case "degree-remove":
      return (
        <ModalInteriorWrapper>
          <ModalTextWrapper>
            <ModalText>{DELETE_CONFIRMATION_MESSAGE("degree")}</ModalText>
          </ModalTextWrapper>
          <ModalButton
            onClick={() => {
              remove_degree(
                (modalObject as RemoveDegreeProps).degreeplanId,
                (modalObject as RemoveDegreeProps).degreeId,
                (modalObject as RemoveDegreeProps).relation
              );
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
