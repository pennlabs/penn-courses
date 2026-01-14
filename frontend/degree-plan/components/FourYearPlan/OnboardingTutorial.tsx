import styled from "@emotion/styled";
import React, { useState, useEffect, useContext, createContext, MutableRefObject } from "react";
import { Cross2Icon } from "@radix-ui/react-icons";

export type TutorialModalKey =
    | "welcome"
    | "requirements-panel-1"
    // | "requirements-panel-2"
    | "edit-requirements"
    | "calendar-panel"
    | "past-semesters"
    | "current-semester"
    | "future-semesters"
    | "edit-mode"
    | "show-stats"
    | "courses-dock"
    | "general-search"
    | null;

// Tutorial steps in order
const TUTORIAL_STEPS: TutorialModalKey[] = [
    "welcome",
    "requirements-panel-1",
    // "requirements-panel-2",
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
];

const MODAL_CONTENT: Record<NonNullable<TutorialModalKey>, { title: string; description: string }> = {
    welcome: {
        title: "Welcome to Penn Degree Plan!",
        description: "Our newest four-year degree planning website, brought to you by Penn Labs."
    },
    "requirements-panel-1": {
        title: "Requirements Panel",
        description: "Requirements for your degree are listed here, organized by majors, school requirements, and electives. Use the dropdown to expand a section and view specific requirements."
    },
    // "requirements-panel-2": {
    //     title: "Requirements Panel",
    //     description: "Requirements for your degree are listed here, organized by majors, school requirements, and electives. Use the dropdown to expand a section and view specific requirements."
    // },
    "edit-requirements": {
        title: "Edit Requirements",
        description: "Add or delete majors by entering edit mode."
    },
    "calendar-panel": {
        title: "Calendar Panel",
        description: "This is an overview of your degree plan by semester. Drag and drop between here and the requirements panel, the courses dock, or between semesters."
    },
    "past-semesters": {
        title: "Past Semesters",
        description: "Gray represents past semesters."
    },
    "current-semester": {
        title: "Current Semester",
        description: "Blue represents the current semester."
    },
    "future-semesters": {
        title: "Future Semesters",
        description: "White represents future semesters."
    },
    "edit-mode": {
        title: "Edit Mode",
        description: "Enter edit mode to add or remove semesters."
    },
    "show-stats": {
        title: "Show Stats",
        description: "Show or hide the course statistics, Course Quality, Instructor Quality, Difficulty, and Work Required."
    },
    "courses-dock": {
        title: "Courses Dock",
        description: "Drag any courses here from the general search, requirements panel, or the schedule panel to view later."
    },
    "general-search": {
        title: "General Search",
        description: "Search for any other courses you would like to be added to electives or to keep on standby."
    }
};

// Component reference mapping
const COMPONENT_REF_MAP: Partial<Record<NonNullable<TutorialModalKey>, string>> = {
    "requirements-panel-1": "reqPanel",
    // "requirements-panel-2": "reqPanel",
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

const ModalBackground = styled.div`
    background-color: #707070;
    opacity: 0.75;
    position: fixed;
    inset: 0;
    z-index: 10;
`;

const ModalContainer = styled.div`
    position: fixed;
    z-index: 40;
    pointer-events: none;
`;

const ModalCard = styled.div<ModalPosition>`
    max-width: 400px;
    max-height: 400px;
    border-radius: 8px;
    box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.3);
    background-color: #fff;
    margin: 0 20px;
    pointer-events: auto;
    position: fixed;
    top: ${props => props.top};
    left: ${props => props.left};
    transform: ${props => props.transform};
`;

const ModalCardHead = styled.header`
    font-weight: 700;
    font-size: 1.4rem;
    padding: 1.5rem 2rem 0.5rem;
    position: relative;
    color: #4a4a4a;
`;

const ModalCardBody = styled.div`
    padding: 0.5rem 2rem 1.5rem;
    overflow: auto;
`;

const ModalInteriorWrapper = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.2rem;
    text-align: center;
`;

const ModalText = styled.div`
    color: var(--modal-text-color);
    font-size: 0.87rem;
    text-align: start;
    width: 100%;
`;

const ButtonRow = styled.div`
    display: flex;
    width: 100%;
    justify-content: flex-end;
    gap: 0.5rem;
`;

const ModalButton = styled.button`
    height: 32px;
    width: 5rem;
    background-color: var(--modal-button-color);
    border-radius: 0.25rem;
    padding: 0.25rem 0.5rem;
    color: white;
    border: none;
    cursor: pointer;
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

type ModalPosition = { top: string; left: string; transform: string };

const MODAL_WIDTH = 400;
const MODAL_HEIGHT = 200;
const SCREEN_PADDING = 20;
const DEFAULT_POSITION: ModalPosition = {
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)"
};

const getComponentRect = (
    modalKey: TutorialModalKey,
    componentRefs: MutableRefObject<Record<string, HTMLElement | null>> | null
): DOMRect | null => {
    if (!modalKey || modalKey === "welcome" || !componentRefs) return null;

    const componentKey = COMPONENT_REF_MAP[modalKey];
    if (!componentKey || !componentRefs.current[componentKey]) return null;

    return componentRefs.current[componentKey]!.getBoundingClientRect();
};

const calculatePositionForKey = (modalKey: NonNullable<TutorialModalKey>, rect: DOMRect): ModalPosition => {
    const positions: Partial<Record<NonNullable<TutorialModalKey>, ModalPosition>> = {
        "requirements-panel-1": {
            top: "50%",
            left: `${rect.left - MODAL_WIDTH - 30}px`,
            transform: "translateY(-50%)"
        },
        // "requirements-panel-2": {
        //     top: "50%",
        //     left: `${rect.left - MODAL_WIDTH - 30}px`,
        //     transform: "translateY(-50%)"
        // },
        "edit-requirements": {
            top: `${rect.top + rect.height + 20}px`,
            left: `${rect.left + rect.width / 2}px`,
            transform: "translateX(-50%)"
        },
        "edit-mode": {
            top: `${rect.bottom + 10}px`,
            left: `${rect.left + rect.width}px`,
            transform: "translateX(-50%)"
        },
        "show-stats": {
            top: `${rect.bottom + 10}px`,
            left: `${rect.left + rect.width / 2}px`,
            transform: "translateX(-50%)"
        },
        "courses-dock": {
            top: `${rect.top - MODAL_HEIGHT + 20}px`,
            left: `${rect.left}px`,
            transform: "translateX(-50%)"
        },
        "general-search": {
            top: `${rect.top - MODAL_HEIGHT + 20}px`,
            left: `${rect.left}px`,
            transform: "translateX(-50%)"
        }
    };

    const calendarPanelKeys = ["calendar-panel", "past-semesters", "current-semester", "future-semesters"];
    if (calendarPanelKeys.includes(modalKey)) {
        return {
            top: `${rect.top + rect.height / 2}px`,
            left: `${rect.right + 10}px`,
            transform: "translateY(-50%)"
        };
    }

    return positions[modalKey] || DEFAULT_POSITION;
};

const constrainToViewport = (position: ModalPosition): ModalPosition => {
    const { innerWidth: windowWidth, innerHeight: windowHeight } = window;

    let { top, left, transform } = position;
    let leftValue = parseInt(left);
    let topValue = parseInt(top);

    if (leftValue + MODAL_WIDTH > windowWidth) {
        left = `${windowWidth - MODAL_WIDTH - SCREEN_PADDING}px`;
        transform = transform.replace("translateX(-50%)", "").replace("translate(-100%, -50%)", "translateY(-50%)");
    } else if (leftValue < SCREEN_PADDING) {
        left = `${SCREEN_PADDING}px`;
        transform = transform.replace("translateX(-50%)", "").replace("translate(-100%, -50%)", "translateY(-50%)");
    }

    if (topValue < SCREEN_PADDING) {
        top = `${SCREEN_PADDING}px`;
        transform = transform.replace("translateY(-50%)", "").replace("translateX(-50%)", "");
    } else if (topValue + MODAL_HEIGHT > windowHeight) {
        top = `${windowHeight - MODAL_HEIGHT - SCREEN_PADDING}px`;
        transform = transform.replace("translateY(-50%)", "").replace("translateX(-50%)", "");
    }

    return { top, left, transform };
};

const calculateModalPosition = (
    modalKey: TutorialModalKey,
    componentRefs: MutableRefObject<Record<string, HTMLElement | null>> | null
): ModalPosition => {
    const rect = getComponentRect(modalKey, componentRefs);
    if (!rect) return DEFAULT_POSITION;

    const position = calculatePositionForKey(modalKey as NonNullable<TutorialModalKey>, rect);
    return constrainToViewport(position);
};

interface TutorialModalContextProps {
    tutorialModalKey: TutorialModalKey;
    setTutorialModalKey: (key: TutorialModalKey) => void;
    highlightedComponentRef: any;
    componentRefs: React.MutableRefObject<Record<string, HTMLElement | null>> | null;
}

export const TutorialModalContext = createContext<TutorialModalContextProps>({
    tutorialModalKey: null,
    setTutorialModalKey: () => { },
    highlightedComponentRef: null,
    componentRefs: null,
});

interface TutorialModalProps {
    updateOnboardingFlag: () => void;
}

const TutorialModal = ({ updateOnboardingFlag }: TutorialModalProps) => {
    const { tutorialModalKey, setTutorialModalKey, componentRefs } = useContext(TutorialModalContext);
    const [position, setPosition] = useState<ModalPosition>(DEFAULT_POSITION);
    const [displayedModalKey, setDisplayedModalKey] = useState<TutorialModalKey>(tutorialModalKey);

    const handleClose = () => {
        updateOnboardingFlag();
        setTutorialModalKey(null);
    };

    const navigateStep = (forward: boolean) => {
        if (!tutorialModalKey) return;

        const currentIndex = TUTORIAL_STEPS.indexOf(tutorialModalKey);
        const nextIndex = forward ? currentIndex + 1 : currentIndex - 1;

        if (nextIndex >= 0 && nextIndex < TUTORIAL_STEPS.length) {
            setTutorialModalKey(TUTORIAL_STEPS[nextIndex]);
        }
    };

    // Update position for next step
    useEffect(() => {
        if (!tutorialModalKey) return;

        const timer = setTimeout(() => {
            const newPosition = calculateModalPosition(tutorialModalKey, componentRefs);
            setPosition(newPosition);
            setDisplayedModalKey(tutorialModalKey);
        }, 20);

        return () => clearTimeout(timer);
    }, [tutorialModalKey, componentRefs]);

    // Handle window resize
    useEffect(() => {
        if (!tutorialModalKey) return;

        const handleResize = () => {
            const newPosition = calculateModalPosition(tutorialModalKey, componentRefs);
            setPosition(newPosition);
        };

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [tutorialModalKey, componentRefs]);

    // Reached last step
    if (!tutorialModalKey) return null;

    const modalContent = displayedModalKey ? MODAL_CONTENT[displayedModalKey] : { title: "", description: "" };
    const isFirstStep = displayedModalKey === "welcome";
    const isLastStep = displayedModalKey === "general-search";

    return (
        <>
            <ModalBackground />
            <ModalContainer>
                <ModalCard top={position.top} left={position.left} transform={position.transform}>
                    <ModalCardHead>
                        {modalContent.title}
                        <CloseButton onClick={handleClose}>
                            <Cross2Icon />
                        </CloseButton>
                    </ModalCardHead>
                    <ModalCardBody>
                        <ModalInteriorWrapper>
                            {isFirstStep && <img src="pdp-porcupine.svg" alt="Porcupine" />}
                            <ModalText>{modalContent.description}</ModalText>
                            <ButtonRow>
                                {!isFirstStep && (
                                    <ModalButton onClick={() => navigateStep(false)}>
                                        Back
                                    </ModalButton>
                                )}
                                {isLastStep ? (
                                    <ModalButton onClick={handleClose}>
                                        Close
                                    </ModalButton>
                                ) : (
                                    <ModalButton onClick={() => navigateStep(true)}>
                                        Next
                                    </ModalButton>
                                )}
                            </ButtonRow>
                        </ModalInteriorWrapper>
                    </ModalCardBody>
                </ModalCard>
            </ModalContainer>
        </>
    );
};

export default TutorialModal;