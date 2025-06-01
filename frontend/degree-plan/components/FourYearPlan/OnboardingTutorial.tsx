import styled from "@emotion/styled";
import React, { useState } from "react";
import ModalContainer from "../common/ModalContainer";
import OnboardingTutorialPanel from "./OnboardingTutorialPanel";
import { createContext } from 'react';

export type TutorialModalKey =
    | "welcome"
    | "requirements-panel-1"
    | "requirements-panel-2"
    // | "search-requirement"
    // | "semester-icons"
    | "edit-requirements"
    | "calendar-panel"
    | "past-semesters"
    | "current-semester"
    | "future-semesters"
    | "edit-mode"
    | "show-stats"
    | "courses-dock"
    | "general-search"
    | null; // null is closed

const getModalTitle = (modalState: TutorialModalKey) => {
    switch (modalState) {
        case "welcome":
            return "Welcome to Penn Degree Plan!";
        case "requirements-panel-1":
            return "Requirements Panel";
        case "requirements-panel-2":
            return "Requirements Panel";
        case "edit-requirements":
            return "Edit Requirements";
        case "calendar-panel":
            return "Calendar Panel";
        case "past-semesters":
            return "Past Semesters";
        case "current-semester":
            return "Current Semester";
        case "future-semesters":
            return "Future Semesters";
        case "edit-mode":
            return "Edit Mode";
        case "show-stats":
            return "Show Stats";
        case "courses-dock":
            return "Courses Dock";
        case "general-search":
            return "General Search";
        case null:
            return "";
    }
};

const getModalDescription = (modalState: TutorialModalKey) => {
    switch (modalState) {
        case "welcome":
            return "Our newest four-year degree planning website, brought to you by Penn Labs.";
        case "requirements-panel-1":
            return "Requirements for your degree are listed here, organized by majors, school requirements, and electives. Use the dropdown to expand a section and view specific requirements.";
        case "requirements-panel-2":
            return "Requirements for your degree are listed here, organized by majors, school requirements, and electives. Use the dropdown to expand a section and view specific requirements.";
        case "edit-requirements":
            return "Add or delete majors by entering edit mode.";
        case "calendar-panel":
            return "This is an overview of your degree plan by semester. Drag and drop between here and the requirements panel, the courses dock, or between semesters.";
        case "past-semesters":
            return "Gray represents past semesters.";
        case "current-semester":
            return "Blue represents the current semester.";
        case "future-semesters":
            return "White represents future semesters.";
        case "edit-mode":
            return "Enter edit mode to add or remove semesters.";
        case "show-stats":
            return "Show or hide the course statistics, Course Quality, Instructor Quality, Difficulty, and Work Required.";
        case "courses-dock":
            return "Drag any courses here from the general search, requirements panel, or the schedule panel to view later.";
        case "general-search":
            return "Search for any other courses you would like to be added to electives or to keep on standby.";
        case null:
            return "";
        default:
            throw Error("Invalid modal key: ");
    }
}

const ModalInteriorWrapper = styled.div<{ $row?: boolean }>`
  display: flex;
  flex-direction: ${(props) => (props.$row ? "row" : "column")};
  align-items: center;
  gap: 1.2rem;
  text-align: center;
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

const ModalBackground = styled.div`
    background-color: #707070;
    opacity: 0.75;
    bottom: 0;
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
    z-index: 10;
`;

interface TutorialModalContextProps {
    tutorialModalKey: TutorialModalKey;
    setTutorialModalKey: (key: TutorialModalKey) => void;
    highlightedComponentRef: any;
    componentRefs: any;
}

export const TutorialModalContext = createContext<TutorialModalContextProps>({
    tutorialModalKey: null,
    setTutorialModalKey: (key: TutorialModalKey) => { }, // placeholder
    highlightedComponentRef: null,
    componentRefs: null,
    // setHighlightedComponent: (component: any) => { } // placeholder
});

interface ModalInteriorProps {
    modalKey: TutorialModalKey;
    nextOnboardingStep: (forward: boolean) => void;
    close: () => void;
}
const ModalInterior = ({
    modalKey,
    nextOnboardingStep,
    close
}: ModalInteriorProps) => {
    if (!modalKey) return <div></div>;

    const topLocation = () => {
        switch (modalKey) {
            case "welcome":
                return "0";
            case "requirements-panel-1":
                return "-40%";
            case "requirements-panel-2":
                return "-30%";
            case "edit-requirements":
                return "-65%";
            case "calendar-panel":
                return "0%";
            case "past-semesters":
                return "20%";
            case "current-semester":
                return "20%";
            case "future-semesters":
                return "20%";
            case "edit-mode":
                return "-65%";
            case "show-stats":
                return "-62%";
            case "courses-dock":
                return "60%";
            case "general-search":
                return "60%";
            case null:
                return "";
            default:
                throw Error("Invalid modal key: ");
        }
    }

    const leftLocation = () => {
        switch (modalKey) {
            case "welcome":
                return "0%";
            case "requirements-panel-1":
                return "-25%";
            case "requirements-panel-2":
                return "-25%";
            case "edit-requirements":
                return "70%";
            case "calendar-panel":
                return "30%";
            case "past-semesters":
                return "-40%";
            case "current-semester":
                return "-10%";
            case "future-semesters":
                return "25%";
            case "edit-mode":
                return "-30%";
            case "show-stats":
                return "-20%";
            case "courses-dock":
                return "-20%";
            case "general-search":
                return "-50%";
            case null:
                return "";
            default:
                throw Error("Invalid modal key: ");
        }
    }

    const arrowLocation = () => {
        switch (modalKey) {
            case "welcome":
                return { top: 0, left: 0 };
            case "requirements-panel-1":
                return { top: 50, left: 50 };
        }
    }

    return (
        <>
            <ModalBackground />
            <OnboardingTutorialPanel title={getModalTitle(modalKey)} position={"absolute"} top={topLocation()} left={leftLocation()} close={close}>
                <ModalInteriorWrapper>
                    {modalKey === "welcome" && <img src="pdp-porcupine.svg" alt="Porcupine" />}
                    <ModalTextWrapper>
                        <ModalText>{getModalDescription(modalKey)}</ModalText>
                    </ModalTextWrapper>
                    <ButtonRow>
                        {modalKey !== "welcome" && <ModalButton onClick={() => nextOnboardingStep(false)}>Back</ModalButton>}
                        {modalKey !== "general-search" && <ModalButton onClick={() => nextOnboardingStep(true)}>Next</ModalButton>}
                        {modalKey === "general-search" && <ModalButton onClick={() => nextOnboardingStep(true)}>Close</ModalButton>}
                    </ButtonRow>
                </ModalInteriorWrapper>
            </OnboardingTutorialPanel>
        </>
    );
};

const TutorialModal = () => {
    const { tutorialModalKey, setTutorialModalKey } = React.useContext(TutorialModalContext);

    const onboardingStep = (forward: boolean) => {
        const steps: TutorialModalKey[] = [
            "welcome",
            "requirements-panel-1",
            "requirements-panel-2",
            "edit-requirements",
            "calendar-panel",
            "past-semesters",
            "current-semester",
            "future-semesters",
            "edit-mode",
            "show-stats",
            "courses-dock",
            "general-search",
            null
        ]
        if (!tutorialModalKey) return "";

        if (forward) {
            const currentIndex = steps.indexOf(tutorialModalKey);
            if (currentIndex < steps.length - 1) {
                setTutorialModalKey(steps[currentIndex + 1]);
            }
        } else {
            const currentIndex = steps.indexOf(tutorialModalKey);
            if (currentIndex > 0) {
                setTutorialModalKey(steps[currentIndex - 1]);
            }
        }
    }

    return (
        // <ModalContainer
        //     title={getModalTitle(modalKey)}
        //     close={() => setModalKey(null)}
        //     modalKey={modalKey}
        // >
        <ModalInterior
            modalKey={tutorialModalKey}
            nextOnboardingStep={(forward: boolean) => onboardingStep(forward)}
            close={() => setTutorialModalKey(null)}
        />
        // </ModalContainer>
    )
};

export default TutorialModal;
