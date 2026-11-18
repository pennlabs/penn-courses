import styled from "@emotion/styled";
import type { DegreeListing, DegreePlan } from "@/types";
import React, { useContext, useState } from "react";
import { postFetcher, useSWRCrud } from "@/hooks/swrcrud";
import { hasConcentration } from "@/utils/programs";
import { useSWRConfig } from "swr";
import Dialog, {
  DialogButton,
  DialogButtons,
  DialogContent,
  DialogInput,
  DialogSubtitle,
  DialogTitle,
} from "../common/Dialog";
import ToastContext from "../Toast/Toast";

export type ModalKey =
  | "plan-create"
  | "plan-rename"
  | "plan-remove"
  | "semester-remove"
  | null; // null is closed

const TITLES: Record<NonNullable<ModalKey>, string> = {
  "plan-create": "Create a new degree plan",
  "plan-rename": "Rename degree plan",
  "plan-remove": "Remove degree plan?",
  "semester-remove": "Remove semester?",
};

const errorText = (error: any, fallback: string) =>
  error?.info?.detail ?? error?.info?.warning ?? fallback;

const NameForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 1rem;
`;

/** Create label for major listings */
export const createMajorLabel = (degree: DegreeListing) => {
  const concentration = hasConcentration(degree.concentration)
    ? ` - ${degree.concentration_name}`
    : "";
  return `${degree.major_name}${concentration}`;
};

interface RemoveSemesterProps {
  helper: () => void;
}

interface ModalInteriorProps {
  modalKey: NonNullable<ModalKey>;
  modalObject: DegreePlan | RemoveSemesterProps | null;
  activeDegreePlan: DegreePlan | null;
  setActiveDegreeplan: (arg0: DegreePlan | null) => void;
  close: () => void;
}

const ModalInterior = ({
  modalObject,
  modalKey,
  activeDegreePlan,
  setActiveDegreeplan,
  close,
}: ModalInteriorProps) => {
  const { update: updateDegreeplan, remove: deleteDegreeplan } = useSWRCrud<
    DegreePlan
  >("/api/degree/degreeplans");
  const { mutate } = useSWRConfig();
  const showToast = useContext(ToastContext);

  const plan = modalObject as DegreePlan | null;
  const [name, setName] = useState(
    modalKey === "plan-rename" ? plan?.name ?? "" : ""
  );
  const trimmedName = name.trim();

  const addDegreeplan = async () => {
    try {
      const created = await postFetcher("/api/degree/degreeplans", {
        name: trimmedName,
      });
      await mutate("/api/degree/degreeplans");
      setActiveDegreeplan(created);
    } catch (error) {
      showToast(
        errorText(error, "Couldn't create the degree plan. Try again."),
        true
      );
    }
  };

  const renameDegreeplan = () => {
    if (!plan) return;
    updateDegreeplan({ name: trimmedName }, plan.id)?.catch((error) =>
      showToast(errorText(error, "Couldn't rename the degree plan."), true)
    );
    if (plan.id == activeDegreePlan?.id)
      setActiveDegreeplan({ ...plan, name: trimmedName });
  };

  const removeDegreeplan = () => {
    if (!plan) return;
    deleteDegreeplan(plan.id).then((deleted) => {
      if (!deleted)
        showToast("Couldn't remove the degree plan. Try again.", true);
    });
  };

  const cancel = (
    <DialogButton type="button" $quiet onClick={close}>
      Cancel
    </DialogButton>
  );

  if (modalKey === "plan-create" || modalKey === "plan-rename") {
    const creating = modalKey === "plan-create";
    return (
      <NameForm
        onSubmit={async (e) => {
          e.preventDefault();
          if (!trimmedName) return;
          if (creating) await addDegreeplan();
          else renameDegreeplan();
          close();
        }}
      >
        <DialogInput
          aria-label="Plan name"
          placeholder={creating ? "Name" : "New name"}
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoFocus
          onFocus={(e) => e.target.select()}
          maxLength={255}
        />
        <DialogButtons>
          {cancel}
          <DialogButton type="submit" disabled={!trimmedName}>
            {creating ? "Create" : "Rename"}
          </DialogButton>
        </DialogButtons>
      </NameForm>
    );
  }

  const removingPlan = modalKey === "plan-remove";
  return (
    <>
      <DialogSubtitle>
        {removingPlan
          ? `“${plan?.name}” and everything planned in it will be deleted.`
          : "All of your planning for this semester will be lost."}
      </DialogSubtitle>
      <DialogButtons>
        {cancel}
        <DialogButton
          type="button"
          $danger
          autoFocus
          onClick={() => {
            if (removingPlan) removeDegreeplan();
            else (modalObject as RemoveSemesterProps).helper();
            close();
          }}
        >
          Remove
        </DialogButton>
      </DialogButtons>
    </>
  );
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
}: DegreeModalProps) => {
  if (!modalKey) return null;
  const close = () => setModalKey(null);
  return (
    <Dialog close={close} label={TITLES[modalKey]} width="23rem">
      <DialogContent>
        <DialogTitle>{TITLES[modalKey]}</DialogTitle>
        <ModalInterior
          modalKey={modalKey}
          modalObject={modalObject}
          activeDegreePlan={activeDegreePlan}
          setActiveDegreeplan={setActiveDegreeplan}
          close={close}
        />
      </DialogContent>
    </Dialog>
  );
};

export default DegreeModal;
