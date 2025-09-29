import styled from "@emotion/styled";
import React, { useState, useEffect, useContext, createContext, MutableRefObject } from "react";
import { Cross2Icon } from "@radix-ui/react-icons";

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

const getModalContent = (modalState: TutorialModalKey) => {
    switch (modalState) {
        case "welcome":
            return {
                title: "Welcome to Penn Degree Plan!",
                description: "Our newest four-year degree planning website, brought to you by Penn Labs."
            };
        case "requirements-panel-1":
        case "requirements-panel-2":
            return {
                title: "Requirements Panel",
                description: "Requirements for your degree are listed here, organized by majors, school requirements, and electives. Use the dropdown to expand a section and view specific requirements."
            };
        case "edit-requirements":
            return {
                title: "Edit Requirements",
                description: "Add or delete majors by entering edit mode."
            };
        case "calendar-panel":
            return {
                title: "Calendar Panel",
                description: "This is an overview of your degree plan by semester. Drag and drop between here and the requirements panel, the courses dock, or between semesters."
            };
        case "past-semesters":
            return {
                title: "Past Semesters",
                description: "Gray represents past semesters."
            };
        case "current-semester":
            return {
                title: "Current Semester",
                description: "Blue represents the current semester."
            };
        case "future-semesters":
            return {
                title: "Future Semesters",
                description: "White represents future semesters."
            };
        case "edit-mode":
            return {
                title: "Edit Mode",
                description: "Enter edit mode to add or remove semesters."
            };
        case "show-stats":
            return {
                title: "Show Stats",
                description: "Show or hide the course statistics, Course Quality, Instructor Quality, Difficulty, and Work Required."
            };
        case "courses-dock":
            return {
                title: "Courses Dock",
                description: "Drag any courses here from the general search, requirements panel, or the schedule panel to view later."
            };
        case "general-search":
            return {
                title: "General Search",
                description: "Search for any other courses you would like to be added to electives or to keep on standby."
            };
        case null:
            return {
                title: "",
                description: ""
            };
        default:
            throw Error("Invalid modal key");
    }
};

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

const ModalContainer = styled.div<{ $top?: string; $left?: string; $position?: string }>`
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    position: ${({ $position }) => $position || "fixed"};
    z-index: 40;
    bottom: 0;
    left: ${({ $left }) => $left || "0"};
    right: 0;
    top: ${({ $top }) => $top || "0"};
    color: #4a4a4a;
`;

const ModalCard = styled.div`
    max-width: 400px !important;
    max-height: 400px !important;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    margin: 0 20px;
    position: relative;
    width: 100%;
    box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.3);
`;

const ModalCardHead = styled.header<{ $center?: boolean }>`
    border: none !important;
    border-bottom: none !important;
    background-color: #fff !important;
    font-weight: 700;
    padding-left: 2rem;
    padding-right: 2rem;
    align-items: center;
    display: flex;
    flex-shrink: 0;
    justify-content: ${({ $center }) => ($center ? "center" : "space-between")};
    padding: 1.5rem;
    padding-bottom: 0.5rem;
    position: relative;
    font-size: 1.4rem;
    margin: 0;
    box-shadow: none;
`;

const ModalCardBody = styled.div`
    padding: 2rem;
    padding-top: 0.5rem;
    padding-bottom: 1.5rem;
    background-color: #fff;
    flex-grow: 1;
    flex-shrink: 1;
    overflow: auto;
    display: block;
    border: none;
`;

const CloseButton = styled.button`
    position: absolute;
    top: 10px;
    right: 10px;
    background: none;
    border: none;
    font-size: 1.2rem;
    font-weight: bold;
    color: #4a4a4a;
    cursor: pointer;

    &:hover {
        color: #000;
    }
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
});

// Function to calculate modal position based on component position
const calculateModalPosition = (modalKey: TutorialModalKey, componentRefs: MutableRefObject<Record<string, HTMLElement | null>> | null) => {
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

interface TutorialModalProps {
    updateOnboardingFlag: () => void;
}

const TutorialModal = ({
    updateOnboardingFlag
}: TutorialModalProps) => {
    const { tutorialModalKey, setTutorialModalKey, componentRefs } = useContext(TutorialModalContext);

    const handleClose = () => {
        updateOnboardingFlag();
        setTutorialModalKey(null);
    }

    const nextOnboardingStep = (forward: boolean) => {
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

    const [position, setPosition] = useState({ top: "50%", left: "50%", transform: "translate(-50%, -50%)" });
    const [displayedModalKey, setDisplayedModalKey] = useState<TutorialModalKey>(tutorialModalKey);

    useEffect(() => {
        if (tutorialModalKey) {
            // Wait until components are rendered, then update position and displayed content together
            const timer = setTimeout(() => {
                const newPosition = calculateModalPosition(tutorialModalKey, componentRefs);
                setPosition(newPosition);
                setDisplayedModalKey(tutorialModalKey);
            }, 20);

            return () => clearTimeout(timer);
        }
    }, [tutorialModalKey, componentRefs]);

    // Window resize
    useEffect(() => {
        const handleResize = () => {
            if (tutorialModalKey) {
                const newPosition = calculateModalPosition(tutorialModalKey, componentRefs);
                setPosition(newPosition);
            }
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [tutorialModalKey, componentRefs]);

    if (!tutorialModalKey) return <div></div>;

    const modalContent = getModalContent(displayedModalKey);

    return (
        <>
            <ModalBackground />
            <ModalContainer $top={position.top} $left={position.left} $position="fixed">
                <div style={{
                    position: "fixed",
                    top: position.top,
                    left: position.left,
                    transform: position.transform,
                    pointerEvents: "auto",
                }}>
                    <ModalCard>
                        <ModalCardHead>
                            <header>{modalContent.title}</header>
                            {handleClose && <CloseButton onClick={handleClose}><Cross2Icon /></CloseButton>}
                        </ModalCardHead>
                        <ModalCardBody>
                            <ModalInteriorWrapper>
                                {displayedModalKey === "welcome" && <img src="pdp-porcupine.svg" alt="Porcupine" />}
                                <ModalTextWrapper>
                                    <ModalText>{modalContent.description}</ModalText>
                                </ModalTextWrapper>
                                <ButtonRow>
                                    {displayedModalKey !== "welcome" && <ModalButton onClick={() => nextOnboardingStep(false)}>Back</ModalButton>}
                                    {displayedModalKey !== "general-search" && <ModalButton onClick={() => nextOnboardingStep(true)}>Next</ModalButton>}
                                    {displayedModalKey === "general-search" && <ModalButton onClick={handleClose}>Close</ModalButton>}
                                </ButtonRow>
                            </ModalInteriorWrapper>
                        </ModalCardBody>
                    </ModalCard>
                </div>
            </ModalContainer>
        </>
    );
};

export default TutorialModal;