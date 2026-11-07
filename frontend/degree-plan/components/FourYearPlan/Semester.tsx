import React, { useState, useRef, useEffect } from "react";
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import CoursesPlanned, { SkeletonCoursesPlanned } from "./CoursesPlanned";
import Stats from "./Stats";
import styled from '@emotion/styled';
import { Course, DegreePlan, DnDCourse, DockedCourse, Fulfillment, GeneratedPlacement, SemesterGenConfig } from "@/types";
import { useSWRCrud } from "@/hooks/swrcrud";
import { TrashIcon } from '../common/TrashIcon';
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'
import { useSWRConfig } from "swr";
import { ModalKey } from "./DegreeModal";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { Tooltip } from 'react-tooltip';
import { useContext } from "react";
import ToastContext from "../Toast/Toast";
import { DisabledTrashIcon } from "../common/DisabledTrashIcon";
import GhostCourse from "./GhostCourse";

const translateSemester = (semester: Course["semester"]) => {
    if (semester === TRANSFER_CREDIT_SEMESTER_KEY) return "AP & Transfer Credit";
    const year = semester.slice(0, 4);
    const term = semester.slice(4);
    return `${term === "A" ? "Spring" : term === "B" ? "Summer" : "Fall"} ${year}`
}

export const SemesterCard = styled.div<{
    $isDroppable: boolean,
    $isOver: boolean,
    $semesterComparison: number // -1 if currentSemester is less than this semester...
}>`
    background: ${props => props.$semesterComparison < 0 ? "#F8F8F8" : props.$semesterComparison === 0 ? "var(--primary-color)" : "#FFFFFF"};
    color: ${props => props.$semesterComparison === 0 ? "var(--primary-color-ultra-dark)" : "inherit"};
    box-shadow: 0px 0px 4px 2px ${props => props.$isOver ? 'var(--selected-color);' : props.$isDroppable ? 'var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
    border-radius: 10px;
    border-width: 0px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    flex: 1 1 11rem;
    min-width: 0;
    container-type: inline-size;

    @container (max-width: 200px) {
        .course-cu,
        .course-actions {
            display: none;
        }
        *:hover > .course-actions,
        .course-actions.open {
            display: inline-flex;
        }
    }
`;

const CollapseToggle = styled.button`
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0;
    border: none;
    background: none;
    font: inherit;
    font-weight: 600;
    color: inherit;
    cursor: pointer;
`;

const CollapsedSummary = styled.span`
    font-weight: 500;
    color: #6b7280;
`;

const SemesterHeader = styled.div`
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
`

const SemesterLabel = styled.div`
    font-weight: 600;
`;

const SemesterContent = styled.div`
    margin-top: 0.75rem;
    min-width: 0;
    display: flex;
    flex-direction: row;
    gap: 1rem;
`;

const FlexStats = styled(Stats)`
    flex-basis: 7rem;
    flex-grow: .1;
`;

const FlexCoursesPlanned = styled(CoursesPlanned)`
    flex-grow: 1;
`;

const CreditsLabel = styled.div<{ $over?: boolean }>`
    font-size: var(--type-body);
    font-weight: 700;
    margin-top: 0.75rem;
    padding-top: 0.4rem;
    border-top: 1px dashed rgba(0, 0, 0, 0.16);
    margin-left: auto;
    margin-right: 0;
    display: flex;
    gap: 0.3rem;
    align-items: center;
    color: ${(props) => (props.$over ? "#e5534b" : "inherit")};
`;

const CapInput = styled.input`
    width: 3.1rem;
    padding: 2px 4px;
    font-size: var(--type-body);
    font-weight: 700;
    text-align: center;
    border: 1px solid rgba(0, 0, 0, 0.16);
    border-radius: 4px;
    background: #fff;
    color: inherit;
`;

const InlineSkeleton = styled(Skeleton)`
    display: inline-block;
`

export const SkeletonSemester = ({
    showStats,
}: { showStats: boolean }) => {
    return (
        <SemesterCard $isDroppable={false} $isOver={false} $semesterComparison={1}>
            <SemesterHeader>
                <SemesterLabel>
                    <Skeleton width="5em" />
                </SemesterLabel>
            </SemesterHeader>
            <SemesterContent>
                <SkeletonCoursesPlanned />
                {!!showStats && <FlexStats fulfillments={[]} />}
            </SemesterContent>
            <CreditsLabel>
                <InlineSkeleton width="2em" /><span>CUs</span>
            </CreditsLabel>
        </SemesterCard>
    )
}

interface SemesterProps {
    showStats: boolean;
    semester: string;
    fulfillments: Fulfillment[]; // fulfillments of this semester
    activeDegreeplanId: DegreePlan["id"] | undefined;
    className?: string;
    editMode: boolean;
    setModalKey: (arg0: ModalKey) => void;
    setModalObject: (obj: any) => void;
    removeSemester: (sem: string) => void;
    currentSemester?: Course["semester"];
    numSemesters: number;
    isLoading?: boolean;
    ghosts?: GeneratedPlacement[];
    genConfig?: SemesterGenConfig;
    onGenConfig?: (next: SemesterGenConfig) => void;
    onPinSlot?: (slotId: string, semester: string) => void;
    onUnpinSlot?: (slotId: string) => void;
    pinnedSlots?: Record<string, string>;
    collapsed?: boolean;
    onToggleCollapsed?: () => void;
}

const FlexSemester = ({
    showStats,
    semester,
    fulfillments,
    activeDegreeplanId,
    editMode,
    setModalKey,
    setModalObject,
    removeSemester,
    currentSemester,
    numSemesters,
    isLoading = false,
    ghosts = [],
    genConfig,
    onGenConfig,
    onPinSlot,
    onUnpinSlot,
    pinnedSlots,
    collapsed = false,
    onToggleCollapsed,
}: SemesterProps) => {
    const showToast = useContext(ToastContext);
    const { mutate } = useSWRConfig();

    const credits = fulfillments.reduce((acc, curr) => acc + (Number(curr.course?.credits) || 1), 0)
    const proposed = ghosts.reduce((acc, ghost) => acc + Number(ghost.cu || 0), 0)
    const isTerm = /^\d{4}[ABC]$/.test(semester)
    const cap = genConfig?.cuCap ?? (semester.endsWith("B") ? 2 : 5.5)

    const { createOrUpdate: addToDock } = useSWRCrud<DockedCourse>(`/api/degree/docked`, { idKey: 'full_code' });

    // the fulfillments api uses the POST method for updates (it creates if it doesn't exist, and updates if it does)
    const { createOrUpdate, remove } = useSWRCrud<Fulfillment>(
        `/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`,
        {
            idKey: "full_code",
            createDefaultOptimisticData: { semester: null, rules: [] }
        }
    );

    const [{ isOver, canDrop }, drop] = useDrop<DnDCourse, never, { isOver: boolean, canDrop: boolean }>(() => ({
        accept: [ItemTypes.COURSE_IN_PLAN, ItemTypes.COURSE_IN_DOCK, ItemTypes.COURSE_IN_REQ, ItemTypes.COURSE_IN_SEARCH, ItemTypes.GHOST],
        drop: (course: DnDCourse & { kind?: string; slot_ids?: string[] }, monitor) => {
            const itemType = monitor.getItemType();
            if (itemType === ItemTypes.GHOST) {
                // A requirement stub stays a stub. Pin it only when it moves to
                // another semester. Dropping it on its current term is not a freeze.
                if (course.kind === "placeholder" && course.slot_ids?.length && course.semester !== semester) {
                    course.slot_ids.forEach((id) => onPinSlot?.(id, semester));
                    return;
                }
                if (course.kind === "placeholder") return;
                if (course.full_code) {
                    createOrUpdate({
                        semester,
                        rules: course.rules || [],
                        from_transcript: false,
                    }, course.full_code);
                }
                return;
            }
            if (itemType === ItemTypes.COURSE_IN_PLAN) { // moved from plan or dock
                createOrUpdate({ semester }, course.full_code);
                return;
            }
            if (itemType === ItemTypes.COURSE_IN_DOCK) {
                course.rule_id = -1;
            }
            fetch(`/api/degree/satisfied-rule-list/${activeDegreeplanId}/${course.full_code}/${course.rule_id}`).then((r) => {
                r.json().then((data) => {
                    const selectedRules = data["selected_rules"].reduce((res: any, obj: any) => {
                        res.push(obj.id);
                        return res;
                    }, []);
                    const unselectedRules = data["unselected_rules"].reduce((res: any, obj: any) => {
                        res.push(obj.id);
                        return res;
                    }, []);
                    
                    createOrUpdate({
                        rules: selectedRules,
                        unselected_rules: unselectedRules,
                        legal: data.legal,
                        semester
                    }, course.full_code);

                    // Toast only if course has been directly dragged from search (not reqpanel!)
                    // TODO: This doesn't work for explicitly listed courses.

                    for (let obj of data["new_selected_rules"]) {
                        if (course.rule_id === -1) {
                            showToast(`${course.full_code} fulfilled ${obj.title}!`, false);
                        } else if (obj.id != course.rule_id) {
                            showToast(`${course.full_code} also fulfilled ${obj.title}!`, false);
                        }
                    }
                })
            })
            return undefined;
        },
        collect: monitor => ({
            isOver: !!monitor.isOver(),
            canDrop: !!monitor.canDrop()
        }),
    }), [createOrUpdate, semester, onPinSlot]);

    const handleRemoveCourse = async (full_code: Course["id"]) => {
        remove(full_code);
        addToDock({ "full_code": full_code }, full_code);
        await mutate(`/api/degree/degreeplans/${activeDegreeplanId}/fulfillments`);
    }

    const removeSemesterHelper = () => {
        removeSemester(semester);
        for (var i = 0; i < fulfillments.length; i++) {
            createOrUpdate({ semester: null }, fulfillments[i].full_code);
        }
    }

    const handleRemoveSemester = () => {
        setModalKey('semester-remove');
        setModalObject({ helper: removeSemesterHelper });
    }

    return (
        <SemesterCard
            id={`semester-${semester}`}
            $isDroppable={canDrop}
            $isOver={isOver}
            ref={drop}
            $semesterComparison={currentSemester ? semester.localeCompare(currentSemester) : 1}
        >
            <SemesterHeader>
                {onToggleCollapsed ? (
                    <CollapseToggle
                        type="button"
                        onClick={onToggleCollapsed}
                        aria-expanded={!collapsed}
                    >
                        <i className={`fas fa-chevron-${collapsed ? "right" : "down"}`} />
                        {translateSemester(semester)}
                        {collapsed && (
                            <CollapsedSummary>{credits.toFixed(1)} CU</CollapsedSummary>
                        )}
                    </CollapseToggle>
                ) : (
                    <SemesterLabel>
                        {translateSemester(semester)}
                    </SemesterLabel>
                )}
                {/* TODO: Current structure doesn't allow for last semester to be deleted.
                    Disabling deletion when there is only one semester 
                    is a quick fix that could be addressed later. */}
                {editMode && (numSemesters > 1 ?
                    <TrashIcon role="button" onClick={handleRemoveSemester}>
                        <i className="fa fa-trash fa-md" />
                    </TrashIcon>
                    : <>
                        <a
                            data-tooltip-id="my-tooltip"
                            data-tooltip-content="You must have at least one semester!"
                        >
                            <DisabledTrashIcon role="button">
                                <i className="fa fa-trash fa-md" />
                            </DisabledTrashIcon>
                        </a>
                        <Tooltip id="my-tooltip" place="top" />
                    </>)
                }
            </SemesterHeader>
            {!collapsed && (<>
            <SemesterContent>
                <FlexCoursesPlanned
                    semester={semester}
                    fulfillments={fulfillments}
                    removeCourse={handleRemoveCourse} />
                {showStats && <FlexStats fulfillments={fulfillments} />}
            </SemesterContent>
            {ghosts.map((ghost) => (
                <GhostCourse
                    key={ghost.slot_ids[0] || `${ghost.kind}-${ghost.full_code}`}
                    placement={ghost}
                    planId={activeDegreeplanId as number}
                    frozen={(ghost.slot_ids || []).some((id) => pinnedSlots?.[id] === semester)}
                    onUnpin={() => (ghost.slot_ids || []).forEach((id) => onUnpinSlot?.(id))}
                />
            ))}
            {editMode && onGenConfig && (
                <label style={{ marginTop: "0.6rem", fontSize: "0.75rem", fontWeight: 600 }}>
                    <input
                        type="checkbox"
                        checked={Boolean(genConfig?.gap)}
                        onChange={(event) => onGenConfig({
                            cuCap: genConfig?.cuCap ?? (semester.endsWith("B") ? 2 : 5.5),
                            gap: event.target.checked,
                        })}
                    />
                    {" "}Gap
                </label>
            )}
            {isTerm ? (
                <CreditsLabel $over={(credits + proposed) > cap + 0.001}>
                    <span>{(credits + proposed).toFixed(1)} /</span>
                    {onGenConfig ? (
                        <CapInput
                            type="number"
                            min="0.5"
                            max="10"
                            step="0.5"
                            aria-label="Semester credit cap"
                            value={cap}
                            onClick={(event) => event.stopPropagation()}
                            onChange={(event) => {
                                const next = Number(event.target.value);
                                if (!Number.isNaN(next) && next > 0) {
                                    onGenConfig({
                                        cuCap: next,
                                        gap: Boolean(genConfig?.gap),
                                    });
                                }
                            }}
                        />
                    ) : (
                        <span>{cap.toFixed(1)}</span>
                    )}
                    <span>CU</span>
                </CreditsLabel>
            ) : (
                <CreditsLabel>
                    {credits.toFixed(1)} CU
                </CreditsLabel>
            )}
            </>)}
        </SemesterCard>
    )
}

export default FlexSemester;
