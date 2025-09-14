import styled from "@emotion/styled";
import React, { useState, useEffect } from "react";
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
    componentRefs: React.MutableRefObject<Record<string, HTMLElement | null>> | null;
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
    componentRefs: any;
}

// Function to calculate modal position based on component position
const calculateModalPosition = (modalKey: TutorialModalKey, componentRefs: React.MutableRefObject<Record<string, HTMLElement | null>> | null) => {
    if (!modalKey || modalKey === "welcome") {
        return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
    }
    if (!componentRefs) return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };

    const componentMap: { [key in NonNullable<TutorialModalKey>]?: string } = {
        "requirements-panel-1": "reqPanel",
        "requirements-panel-2": "reqPanel",
        "edit-requirements": "editReqs",
        "calendar-panel": "planPanel",
        "past-semesters": "planPanel",
        "current-semester": "planPanel",
        "future-semesters": "planPanel",
        "edit-mode": "editSemesterButton",
        "show-stats": "showStatsButton",
        "courses-dock": "dock",
        "general-search": "dock",
    };

    const componentKey = componentMap[modalKey as NonNullable<TutorialModalKey>];
    if (!componentKey || !componentRefs.current[componentKey]) {
        // Fallback to center if component not found
        return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
    }

    const component = componentRefs.current[componentKey];
    const rect = component.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;

    const modalWidth = 400;
    const modalHeight = 200;

    // Calculate position based on component location
    let top: string;
    let left: string;
    let transform = "";

    switch (modalKey) {
        case "requirements-panel-1":
        case "requirements-panel-2":
            top = `${rect.top + rect.height / 2}px`;
            left = `${rect.left - modalWidth - 30}px`;
            transform = "translateY(-50%)";
            break;
        case "edit-requirements":
            top = `${rect.top + rect.height + 20}px`;
            left = `${rect.left + rect.width / 2}px`;
            transform = "translateX(-50%)";
            break;
        case "calendar-panel":
        case "past-semesters":
        case "current-semester":
        case "future-semesters":
            top = `${rect.top + rect.height / 2}px`;
            left = `${rect.right + 10}px`;
            transform = "translateY(-50%)";
            break;
        case "edit-mode":
            top = `${rect.bottom + 10}px`;
            left = `${rect.left + rect.width / 2}px`;
            transform = "translateX(-50%)";
            break;
        case "show-stats":
            top = `${rect.bottom + 10}px`;
            left = `${rect.left + rect.width / 2}px`;
            transform = "translateX(-50%)";
            break;
        case "courses-dock":
        case "general-search":
            top = `${rect.top - modalHeight + 20}px`;
            left = `${rect.left}px`;
            transform = "translateX(-50%)";
            break;
        default:
            return { top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
    }

    // Adjust position if off-screen
    const leftValue = parseInt(left);
    if (leftValue + modalWidth > windowWidth) {
        left = `${windowWidth - modalWidth - 20}px`;
        transform = transform.replace("translateX(-50%)", "").replace("translate(-100%, -50%)", "translateY(-50%)");
    } else if (leftValue < 20) {
        left = "20px";
        transform = transform.replace("translateX(-50%)", "").replace("translate(-100%, -50%)", "translateY(-50%)");
    }

    const topValue = parseInt(top);
    if (topValue < 20) {
        top = "20px";
        transform = transform.replace("translateY(-50%)", "").replace("translateX(-50%)", "");
    } else if (topValue + modalHeight > windowHeight) {
        top = `${windowHeight - modalHeight - 20}px`;
        transform = transform.replace("translateY(-50%)", "").replace("translateX(-50%)", "");
    }

    return { top, left, transform };
};

const ModalInterior = ({
    modalKey,
    nextOnboardingStep,
    close,
    componentRefs
}: ModalInteriorProps) => {
    const [position, setPosition] = useState({ top: "50%", left: "50%", transform: "translate(-50%, -50%)" });

    useEffect(() => {
        if (modalKey) {
            // wait until components are rendered
            const timer = setTimeout(() => {
                const newPosition = calculateModalPosition(modalKey, componentRefs);
                setPosition(newPosition);
            }, 20);

            return () => clearTimeout(timer);
        }
    }, [modalKey, componentRefs]);

    // Window resize
    useEffect(() => {
        const handleResize = () => {
            if (modalKey) {
                const newPosition = calculateModalPosition(modalKey, componentRefs);
                setPosition(newPosition);
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [modalKey, componentRefs]);

    if (!modalKey) return <div></div>;

    return (
        <>
            <ModalBackground />
            <OnboardingTutorialPanel
                title={getModalTitle(modalKey)}
                position="fixed"
                top={position.top}
                left={position.left}
                transform={position.transform}
                close={close}
            >
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
    const { tutorialModalKey, setTutorialModalKey, componentRefs } = React.useContext(TutorialModalContext);

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
        <ModalInterior
            modalKey={tutorialModalKey}
            nextOnboardingStep={(forward: boolean) => onboardingStep(forward)}
            close={() => setTutorialModalKey(null)}
            componentRefs={componentRefs}
        />
    )
};

export default TutorialModal;
