import styled from "@emotion/styled";
import type {
  Degree,
  DegreeListing,
  DegreePlan,
  MajorOption,
  SchoolOption,
} from "@/types";
import React, { useState, useEffect } from "react";
import { deleteFetcher, postFetcher, useSWRCrud, getCsrf, normalizeFinalSlash } from "@/hooks/swrcrud";
import useSWR, { useSWRConfig } from "swr";
import ModalContainer from "../common/ModalContainer";
import Select from "react-select";
import { schoolOptions } from "@/components/OnboardingPanels/SharedComponents";
import { ErrorText } from "@/components/OnboardingPanels/SharedComponents";
import { assertValueType } from "@/types";

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

  const { data: degrees, isLoading: isLoadingDegrees } = useSWR<
    DegreeListing[]
  >(`/api/degree/degrees`);

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
    } catch (error) {
      console.error(error);
    } finally {
      setIsAddingDegree(false);
    }
  };

  const remove_degree = async (degreeplanId: number, degreeId: number) => {
    await deleteFetcher(`/api/degree/degreeplans/${degreeplanId}/degrees`, {
      degree_ids: [degreeId],
    }); // remove degree
    await mutate(`/api/degree/degreeplans/${degreeplanId}`); // use updated degree plan returned
  };



  // Update degree plan handling error case where degree plan of same name already exists.
  const [sameNameError, setSameNameError] = useState(false);

  const updateDegreeplanWithErrorHandling = async (updatedData: Partial<DegreePlan>, id: number | string | null) => {
    if (!id) return;

    const key = normalizeFinalSlash(`/api/degree/degreeplans/${id}`);
    const res = await fetch(key, {
      credentials: "include",
      mode: "same-origin",
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrf(),
        "Accept": "application/json",
      } as HeadersInit,
      body: JSON.stringify({ name: name }),
    });

    if (res.ok) {
      const updated = await res.json();

      // Handle mutation
      // Code adapted from swrcrud.ts
      const idKey = "id" as keyof DegreePlan;

      mutate(key, updated, {
        optimisticData: (data?: DegreePlan) => {
            const optimistic = {...data, ...updatedData} as DegreePlan;
            assertValueType(optimistic, idKey, id)
            optimistic.id = Number(id); // does this work?
            return ({ id, ...data, ...updatedData} as DegreePlan)
        },
        revalidate: false,
        throwOnError: false
      })

      const endpoint = "/api/degree/degreeplans";
      mutate(endpoint, updated, {
        optimisticData: (list?: Array<DegreePlan>) => {
            if (!list) return [];
            const index = list.findIndex((item: DegreePlan) => String(item[idKey]) === id);
            if (index === -1) {
                mutate(endpoint) // trigger revalidation
                return list;
            }
            list.splice(index, 1, {...list[index], ...updatedData});
            return list;
        },
        populateCache: (updated: DegreePlan, list?: Array<DegreePlan>) => {
            if (!list) return [];
            if (!updated) return list;
            const index = list.findIndex((item: DegreePlan) => item[idKey] === updated[idKey]);
            if (index === -1) {
                console.warn("swrcrud: update: updated element not found in list view");
                mutate(endpoint); // trigger revalidation
                return list;
            }
            list.splice(index, 1, updated);
            return list
        },
        revalidate: false,
        throwOnError: false
      })

      close(); // only close if update is successful
    } else if (res.status === 409) {
      setSameNameError(true);

      setTimeout(() => {
        setSameNameError(false);
      }, 5000);
    } else {
      throw new Error(await res.text());
    }
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
                updateDegreeplanWithErrorHandling({name: name}, modalObject.id);
                if (modalObject.id == activeDegreePlan?.id) {
                  let newNameDegPlan = modalObject;
                  newNameDegPlan.name = name;
                  setActiveDegreeplan(newNameDegPlan);
                }
              } else {
                close();
              }
            }}
          >
            Rename
          </ModalButton>
          {sameNameError && <ErrorText style={{ color: "red" }}>A degree plan with this name already exists.</ErrorText>}
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
            </SelectList>
            <ButtonRow $center={true}>
              <ModalButton
                disabled={isAddingDegree}
                onClick={async () => {
                  if (!major?.value.id) return;
                  await add_degree((modalObject as Degree).id, major?.value.id);
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
                (modalObject as RemoveDegreeProps).degreeId
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
