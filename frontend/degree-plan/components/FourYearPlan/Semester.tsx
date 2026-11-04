import React, { useState, useRef, useEffect } from "react";
import { useDrag, useDrop } from "react-dnd";
import { ItemTypes } from "../Dock/dnd/constants";
import CoursesPlanned, { SkeletonCoursesPlanned } from "./CoursesPlanned";
import Stats from "./Stats";
import styled from '@emotion/styled';
import { Course, DegreePlan, DnDCourse, DockedCourse, Fulfillment } from "@/types";
import { useSWRCrud } from "@/hooks/swrcrud";
import { TrashIcon } from '../common/TrashIcon';
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'
import { mutate } from "swr";
import { ModalKey } from "./DegreeModal";
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { Tooltip } from 'react-tooltip';
import { useContext } from "react";
import ToastContext from "../Toast/Toast";
import { DisabledTrashIcon } from "../common/DisabledTrashIcon";
import { SearchPanelContext } from "../Search/SearchPanel";

const translateSemester = (semester: Course["semester"]) => {
    if (semester === TRANSFER_CREDIT_SEMESTER_KEY) return "AP & Transfer Credit";
    const year = semester.slice(0, 4);
    const term = semester.slice(4);
    return `${term === "A" ? "Spring" : term === "B" ? "Summer" : "Fall"} ${year}`
}

// A semester shows about a full course load until it's expanded.
const COLLAPSED_CREDITS = 5;

const courseCredits = (fulfillment: Fulfillment) => fulfillment.course?.credits || 1; // default to 1 cu

const totalCredits = (fulfillments: Fulfillment[]) =>
    fulfillments.reduce((acc, curr) => acc + courseCredits(curr), 0);

const formatCredits = (credits: number) =>
    Number.isInteger(credits) ? `${credits}` : credits.toFixed(1);

/** The leading courses that fit in `limit` credits, always including the first. */
const coursesWithinCredits = (fulfillments: Fulfillment[], limit: number) => {
    const shown: Fulfillment[] = [];
    let credits = 0;
    for (const fulfillment of fulfillments) {
        const next = credits + courseCredits(fulfillment);
        if (shown.length > 0 && next > limit) break;
        shown.push(fulfillment);
        credits = next;
        if (credits >= limit) break;
    }
    return shown;
};

export const SemesterCard = styled.div<{
    $isDroppable: boolean,
    $isOver: boolean,
    $semesterComparison: number, // -1 if currentSemester is less than this semester...
    $isTransfer?: boolean,
}>`
    background: ${props => props.$semesterComparison < 0 ? "var(--background-light-grey)" : props.$semesterComparison === 0 ? "var(--primary-color)" : "#FFFFFF"};
    color: ${props => props.$semesterComparison === 0 ? "var(--primary-color-ultra-dark)" : "inherit"};
    box-shadow: 0px 0px 4px 2px ${props => props.$isOver ? 'var(--selected-color);' : props.$isDroppable ? 'var(--primary-color-dark);' : 'rgba(0, 0, 0, 0.05);'}
    border-radius: 16px;
    border-width: 0px;
    padding: 1.1rem 1.15rem .9rem;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    max-width: 100%;
    ${props => props.$isTransfer
        ? "flex: 1 1 100%; order: -1;"
        : "flex: 1 1 15rem; min-width: min(100%, 15rem);"}
    transition: box-shadow 150ms ease-out;
`;

const SemesterHeader = styled.div`
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    min-height: 1.75rem; /* keeps titles aligned across a row, with or without header buttons */
`

const SemesterLabel = styled.div<{ $isCurrent?: boolean }>`
    font-weight: 700;
    font-size: 1.05rem;
    color: ${props => props.$isCurrent ? "var(--primary-color-ultra-dark)" : "#2f2f2f"};
`;

const TransferToggle = styled.button`
    display: inline-flex;
    align-items: center;
    gap: .5rem;
    border: none;
    padding: 0;
    background: none;
    text-align: left;

    i {
        font-size: .8rem;
        color: var(--primary-color-xxx-dark);
    }
`;

const HeaderActions = styled.div`
    display: inline-flex;
    align-items: center;
    gap: .25rem;
`;

const CollapsedCredits = styled.span`
    font-size: .9rem;
    font-weight: 600;
    color: #4a4a4a;
    white-space: nowrap;
`;

const CollapseButton = styled.button`
    border: none;
    border-radius: 5px;
    background: none;
    padding: .25rem .4rem;
    font-size: .85rem;
    line-height: 1;
    color: var(--primary-color-xxx-dark);

    &:hover {
        background: rgba(108, 114, 182, 0.12);
        color: var(--primary-color-ultra-dark);
    }
`;

const SemesterContent = styled.div`
    margin-top: .85rem;
    display: flex;
    flex-direction: column;
    gap: .85rem;
    flex: 1;
    width: 100%;
    min-width: 0;
`;

const CoursesArea = styled.div<{ $isOver: boolean }>`
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    gap: .5rem;
    border-radius: 12px;
    transition: box-shadow 150ms ease-out, background 150ms ease-out;
    ${props => props.$isOver
        ? "background: rgba(150, 123, 182, 0.06); box-shadow: 0 0 0 .4rem rgba(150, 123, 182, 0.06), 0 0 0 calc(.4rem + 1.5px) var(--selected-color);"
        : ""}
`;

const EmptyCourses = styled.div`
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 7.5rem;
    padding: .65rem;
    border: 1.5px solid #d8d8d8;
    border-radius: 12px;
`;

const AddCourseButton = styled.button`
    border: none;
    border-radius: 8px;
    background: none;
    padding: .5rem .75rem;
    font-size: .95rem;
    font-weight: 500;
    line-height: 1.2;
    color: #b0b0b0;

    &:hover {
        color: var(--primary-color-xxx-dark);
        background: rgba(108, 114, 182, 0.08);
    }
`;

const ShowMoreButton = styled.button`
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 28px;
    border: none;
    border-radius: 7px;
    padding: .35rem .5rem;
    font-size: .8rem;
    font-weight: 600;
    color: var(--primary-color-xxx-dark);
    background: var(--primary-color-light);

    &:hover {
        background: var(--primary-color-dark);
        color: var(--primary-color-ultra-dark);
    }
`;

const CreditsLabel = styled.div`
    margin-top: .85rem;
    margin-left: auto;
    margin-right: 0;
    display: flex;
    gap: .3rem;
    align-items: baseline;
    font-size: .95rem;
    font-weight: 500;
    color: #4a4a4a;

    strong {
        font-weight: 700;
    }
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
                {!!showStats && <Stats fulfillments={[]} />}
                <SkeletonCoursesPlanned />
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
    animateCourses?: boolean;
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
    animateCourses = false
}: SemesterProps) => {
    const showToast = useContext(ToastContext);
    const { setSearchPanelOpen, setSearchRuleQuery, setSearchRuleId } = useContext(SearchPanelContext);

    const isTransfer = semester === TRANSFER_CREDIT_SEMESTER_KEY;
    const semesterComparison = currentSemester ? semester.localeCompare(currentSemester) : 1;

    const credits = totalCredits(fulfillments);

    const [expanded, setExpanded] = useState(false);
    const [transferOpen, setTransferOpen] = useState(false); // transfer credit starts collapsed

    const withinCap = coursesWithinCredits(fulfillments, COLLAPSED_CREDITS);
    const overflows = !isTransfer && withinCap.length < fulfillments.length;
    const shownCourses = overflows && !expanded ? withinCap : fulfillments;
    const hiddenCourses = fulfillments.slice(shownCourses.length);
    const showBody = !isTransfer || transferOpen;

    const openSearch = () => {
        setSearchRuleQuery("");
        setSearchRuleId(null);
        setSearchPanelOpen(true);
    };

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
        accept: [ItemTypes.COURSE_IN_PLAN, ItemTypes.COURSE_IN_DOCK, ItemTypes.COURSE_IN_REQ, ItemTypes.COURSE_IN_SEARCH],
        drop: (course: DnDCourse, monitor) => {
            // A course dropped here shouldn't disappear behind a collapsed list.
            setExpanded(true);
            setTransferOpen(true);
            const itemType = monitor.getItemType();
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
    }), [createOrUpdate, semester]);

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
            $isDroppable={canDrop}
            $isOver={isOver}
            ref={drop}
            $semesterComparison={semesterComparison}
            $isTransfer={isTransfer}
        >
            <SemesterHeader>
                {isTransfer ? (
                    <TransferToggle
                        type="button"
                        aria-expanded={transferOpen}
                        onClick={() => setTransferOpen(!transferOpen)}
                    >
                        <SemesterLabel>{translateSemester(semester)}</SemesterLabel>
                        <i className={`fas fa-chevron-${transferOpen ? "up" : "down"}`} aria-hidden />
                    </TransferToggle>
                ) : (
                    <SemesterLabel $isCurrent={semesterComparison === 0}>
                        {translateSemester(semester)}
                    </SemesterLabel>
                )}
                <HeaderActions>
                    {!showBody && <CollapsedCredits>{formatCredits(credits)} CUs</CollapsedCredits>}
                    {overflows && (
                        <CollapseButton
                            type="button"
                            aria-expanded={expanded}
                            aria-label={`${expanded ? "Collapse" : "Expand"} ${translateSemester(semester)}`}
                            onClick={() => setExpanded(!expanded)}
                        >
                            <i className={`fas fa-chevron-${expanded ? "up" : "down"}`} aria-hidden />
                        </CollapseButton>
                    )}
                    {/* TODO(el-agua): allow deleting the last semester. */}
                    {editMode && !isTransfer && (numSemesters > 1 ?
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
                </HeaderActions>
            </SemesterHeader>
            {showBody && (
                <>
                    <SemesterContent>
                        {showStats && <Stats fulfillments={fulfillments} />}
                        <CoursesArea $isOver={isOver}>
                            {fulfillments.length === 0 ? (
                                <EmptyCourses>
                                    <AddCourseButton type="button" onClick={openSearch}>
                                        + Add Course
                                    </AddCourseButton>
                                </EmptyCourses>
                            ) : (
                                <>
                                    <CoursesPlanned
                                        semester={semester}
                                        fulfillments={shownCourses}
                                        removeCourse={handleRemoveCourse}
                                        animate={animateCourses} />
                                    {overflows && (
                                        <ShowMoreButton type="button" onClick={() => setExpanded(!expanded)}>
                                            {expanded
                                                ? "Show less"
                                                : `+${hiddenCourses.length} more · ${formatCredits(totalCredits(hiddenCourses))} CUs`}
                                        </ShowMoreButton>
                                    )}
                                </>
                            )}
                        </CoursesArea>
                    </SemesterContent>
                    <CreditsLabel>
                        <strong>{formatCredits(credits)}</strong>
                        <span>CUs</span>
                    </CreditsLabel>
                </>
            )}
        </SemesterCard>
    )
}

export default FlexSemester;