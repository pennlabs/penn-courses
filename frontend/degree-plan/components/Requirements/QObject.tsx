import type { DegreePlan, Fulfillment, Rule } from "@/types";
import styled from "@emotion/styled";
import { Icon } from "../common/bulma_derived_components";
import CourseInPlan from "../FourYearPlan/CourseInPlan";
import { SkeletonCourse } from "../Course/Course";
import assert from "assert";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { SearchPanelContext } from "../Search/SearchPanel";
import CourseInReq from "./CourseInReq";
import {
  ExpandedCoursesPanelContext,
  ExpandedCoursesPanelTrigger,
} from "@/components/ExpandedBox/ExpandedCoursesPanelTrigger";import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";

const interpolate = <T,>(arr: T[], separator: T) =>
    arr.flatMap(
        (elem, index) => index < arr.length - 1 ?
            [elem, separator]
            : [elem]
    )


type ConditionKey = "full_code" | "semester" | "attributes__code__in" | "department__code" | "full_code__startswith" | "code__gte" | "code__lte" | "department__code__in" | "code"
interface Condition {
    type: 'LEAF';
    key: ConditionKey;
    value: string | number | boolean | null | string[];
}

// represents a course requirement
interface QCourse {
    type: 'COURSE';
    full_code: string;
    semester?: string;
}
interface Search {
    type: 'SEARCH';
    q: ParsedQObj
}
interface And {
    type: 'AND';
    clauses: (Compound | Condition | QCourse | Search)[];
}

interface Or {
    type: 'OR';
    clauses: (Compound | Condition | QCourse | Search)[];
}
type Compound = Or | And;

type ParsedQObj = Condition | Compound | QCourse | Search;
type TransformedQObject = QCourse | Search | Or;

/** A requirements row lists courses up to this many. Past it, the row is a search. */
export const SHORT_LIST_MAX = 8;

export interface PanelOption {
    count: number;
    courses?: string[];
}

export const PanelOptionsContext = createContext<Record<string, PanelOption>>({});


const Row = styled.div<{ $wrap?: boolean, $gap?: string, $inline?: boolean }>`
    display: flex;
    flex-direction: row;
    gap: ${({ $gap }) => $gap ? $gap : "0.5rem"};
    align-items: center;
    width: ${({ $inline }) => $inline ? "auto" : "100%"};
    flex: ${({ $inline }) => $inline ? "1 1 auto" : "unset"};
    min-width: 0;
    max-width: 100%;
    flex-wrap: ${({ $wrap }) => $wrap ? "wrap" : "nowrap"};
`;

const SearchConditionRow = styled.div`
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
    min-width: 0;
    max-width: 100%;
`;

const SearchChip = styled.button<{ $active: boolean }>`
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    max-width: 100%;
    padding: 0.35rem 0.65rem;
    min-height: 28px;
    border-radius: 9px;
    border: 1px dashed ${(props) => (props.$active ? "#3d4ed8" : "rgba(98, 116, 241, 0.55)")};
    background: ${(props) => (props.$active ? "rgba(98, 116, 241, 0.16)" : "rgba(98, 116, 241, 0.08)")};
    color: #3d4ed8;
    font: inherit;
    font-size: var(--type-body);
    font-weight: 600;
    line-height: 1.35;
    cursor: pointer;
    white-space: nowrap;

    span {
        overflow: hidden;
        text-overflow: ellipsis;
    }

    i {
        font-size: 0.75em;
    }
`;

const DarkGrayIcon = styled(Icon)`
    color: #575757;
    fill: #575757;
`

export const DarkBlueIcon = styled(Icon)`
    color: var(--primary-color-extra-dark);
`

interface SearchConditionInnerProps {
    q: ParsedQObj;
}
const ExpandOrRetractIcon = ({ showExpand }: { showExpand: boolean }) => {
    return (
        <DarkGrayIcon>
            {showExpand ?
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="12" height="12">
                    <path d="M344 0L488 0c13.3 0 24 10.7 24 24l0 144c0 9.7-5.8 18.5-14.8 22.2s-19.3 1.7-26.2-5.2l-39-39-87 87c-9.4 9.4-24.6 9.4-33.9 0l-32-32c-9.4-9.4-9.4-24.6 0-33.9l87-87L327 41c-6.9-6.9-8.9-17.2-5.2-26.2S334.3 0 344 0zM168 512L24 512c-13.3 0-24-10.7-24-24L0 344c0-9.7 5.8-18.5 14.8-22.2s19.3-1.7 26.2 5.2l39 39 87-87c9.4-9.4 24.6-9.4 33.9 0l32 32c9.4 9.4 9.4 24.6 0 33.9l-87 87 39 39c6.9 6.9 8.9 17.2 5.2 26.2s-12.5 14.8-22.2 14.8z" />
                </svg>
                : <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="12" height="12">
                    <path d="M439 7c9.4-9.4 24.6-9.4 33.9 0l32 32c9.4 9.4 9.4 24.6 0 33.9l-87 87 39 39c6.9 6.9 8.9 17.2 5.2 26.2s-12.5 14.8-22.2 14.8l-144 0c-13.3 0-24-10.7-24-24l0-144c0-9.7 5.8-18.5 14.8-22.2s19.3-1.7 26.2 5.2l39 39L439 7zM72 272l144 0c13.3 0 24 10.7 24 24l0 144c0 9.7-5.8 18.5-14.8 22.2s-19.3 1.7-26.2-5.2l-39-39L73 505c-9.4 9.4-24.6 9.4-33.9 0L7 473c-9.4-9.4-9.4-24.6 0-33.9l87-87L55 313c-6.9-6.9-8.9-17.2-5.2-26.2s12.5-14.8 22.2-14.8z" />
                </svg>
            }
        </DarkGrayIcon>
    )
}

interface SearchConditionProps extends SearchConditionInnerProps {
    fulfillments: Fulfillment[]
    unselectedFulfillments: Fulfillment[]
    ruleIsSatisfied: boolean,
    ruleId: Rule["id"];
    ruleQuery: string;
    activeDegreeplanId: DegreePlan["id"];
    num: number | null;
    cu: number | null;
    count?: number;
    showCode?: boolean;
}
const SearchCondition = ({ cu, num, ruleId, ruleQuery, fulfillments, unselectedFulfillments, ruleIsSatisfied, q, activeDegreeplanId }: SearchConditionProps) => {
    const { setSearchPanelOpen, searchRuleId, setSearchRuleQuery, setSearchRuleId, setSearchFulfillments, } = useContext(SearchPanelContext);
    
    const { searchRef } = useContext(ExpandedCoursesPanelContext);

    // TODO: Pls make this less janky. Needed to make it such that clicking off of popup changes
    // arrows to right direction, but had issues if user clicked directly on the arrows to close them
    // (as setToExpand()) would cancel out. This is a workaround, but it's pretty hacky.
    const [toExpand, setToExpand] = useState(true);
    const [canExpandAgain, setCanExpandAgain] = useState(true);

    const ref = useRef(null);

    useEffect(() => {
        if (toExpand)
            setTimeout(() => {
                setCanExpandAgain(true)
        }, 75)
    }, [toExpand])

    const text = "Search";

    return (

        <SearchConditionRow ref={ref}>
            {unselectedFulfillments.length > 0 || (num && fulfillments.length + unselectedFulfillments.length > num) || (cu && fulfillments.length + unselectedFulfillments.length > cu) ?
                <span onClick={() => {if (toExpand && canExpandAgain) {setToExpand(false); setCanExpandAgain(false)}}}>
                    <ExpandedCoursesPanelTrigger searchRef={ref} courses={unselectedFulfillments} ruleId={ruleId} changeExpandIcon={() => {setToExpand(true)}} triggerType="click">
                        <ExpandOrRetractIcon showExpand={toExpand} />
                    </ExpandedCoursesPanelTrigger>
                 </span>
            : null}
            <SearchChip
                type="button"
                $active={searchRuleId == ruleId}
                aria-label="Search courses"
                onClick={() => {
                    setSearchRuleQuery(ruleQuery);
                    if ((q.type === "OR" || q.type === "AND") && q.clauses.length == 0) {
                        setSearchRuleId(null);
                    } else {
                        setSearchRuleId(ruleId)
                    }
                    setSearchPanelOpen(true);
                    setSearchFulfillments(fulfillments)
                }}
            >
                <i className="fas fa-search" aria-hidden="true" />
                {text ? <span>{text}</span> : null}
            </SearchChip>
            {fulfillments.map(fulfillment => (
                <CourseInReq course={fulfillment} ruleId={ruleId} fulfillment={fulfillment} isDisabled={ruleIsSatisfied} isOpenEnded isUsed activeDegreePlanId={activeDegreeplanId} />
            ))}
        </SearchConditionRow>
    )
}

const CourseOptionsSeparator = styled.div`
    font-size: var(--type-body);
    text-transform: lowercase;
    color: #94a3b8;
    font-weight: 600;
`;

const OptionChipRow = styled.div<{ $scroll?: boolean }>`
    display: flex;
    flex: ${(props) => (props.$scroll ? "1 1 0" : "1 1 auto")};
    flex-wrap: ${(props) => (props.$scroll ? "nowrap" : "wrap")};
    gap: 2px;
    align-items: center;
    width: ${(props) => (props.$scroll ? "auto" : "100%")};
    min-width: 0;
    max-width: 100%;
    overflow-x: ${(props) => (props.$scroll ? "auto" : "visible")};
    overflow-y: hidden;
    scrollbar-width: thin;
`;

const OptionChip = styled.span<{ $kind: "open" | "taken" | "frozen" }>`
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: var(--type-body);
    font-weight: 600;
    padding: 0.35rem 0.65rem;
    min-height: 28px;
    border-radius: 9px;
    white-space: nowrap;
    border: 1px solid ${(props) =>
        props.$kind === "taken" ? "rgba(34, 197, 94, 0.45)"
        : props.$kind === "frozen" ? "#d97706"
        : "rgba(0, 0, 0, 0.14)"};
    background: ${(props) =>
        props.$kind === "taken" ? "rgba(34, 197, 94, 0.12)"
        : props.$kind === "frozen" ? "rgba(217, 119, 6, 0.12)"
        : "#fff"};
    color: ${(props) =>
        props.$kind === "taken" ? "#15803d"
        : props.$kind === "frozen" ? "#b45309"
        : "#4b5563"};
`;

const CourseOptionChips = ({ options, fulfillments }: { options: QCourse[]; fulfillments: Fulfillment[] }) => {
    const byCode = new Map(fulfillments.map((row) => [row.full_code, row]));
    return (
        <OptionChipRow $scroll={options.length > 3}>
            {options.map((course) => {
                const fulfillment = byCode.get(course.full_code);
                const chosen = course.semester
                    ? fulfillment?.semester === course.semester
                    : !!fulfillment;
                const kind = chosen && fulfillment
                    ? fulfillment.from_transcript ? "taken" : "frozen"
                    : "open";
                return (
                    <OptionChip key={`${course.full_code}-${course.semester || ""}`} $kind={kind}>
                        {course.full_code.replace(/-/g, " ")}
                    </OptionChip>
                );
            })}
        </OptionChipRow>
    );
};

const transformCourseClauses = (q: ParsedQObj): ParsedQObj => {
    if (q.type === "LEAF" && q.key === "full_code") return { type: "COURSE", full_code: q.value as string };
    if (q.type === "AND" && q.clauses.length == 2) {
        const semester = (q.clauses.find((clause) => clause.type === "LEAF" && clause.key === "semester") as Condition | undefined)?.value as string | undefined;
        const full_code = (q.clauses.find((clause) => clause.type === "LEAF" && clause.key === "full_code") as Condition | undefined)?.value as string | undefined;
        if (full_code) return { type: "COURSE", semester, full_code };
    }
    // parse recursively
    if (q.type === "AND" || q.type === "OR") return { ...q, clauses: q.clauses.map(transformCourseClauses) }
    return q;
}
const transformDepartmentInClauses = (q: ParsedQObj): ParsedQObj => {
    if (q.type === "LEAF" && q.key === "department__code__in") return {
        type: "OR",
        clauses: (q.value as string[]).map(dept => ({ type: "LEAF", key: "department__code", value: dept }))
    };
    if (q.type === "AND" || q.type === "OR") return { ...q, clauses: q.clauses.map(transformDepartmentInClauses) }
    return q;
}
const transformSearchConditions = (q: ParsedQObj): ParsedQObj => {
    if (q.type === "COURSE") return q;
    if (q.type !== "OR") return { type: "SEARCH", q };

    // combine together search conditions
    let clauses = q.clauses.map(transformSearchConditions);
    const searchConditions = clauses.filter((clause) => clause.type === "SEARCH") as Search[];
    clauses = clauses.filter((clause) => clause.type !== "SEARCH")

    if (searchConditions.length === 1) clauses.push(searchConditions[0]);
    else if (searchConditions.length > 1) clauses.push({
        type: "SEARCH",
        q: {
            type: "OR",
            clauses: searchConditions.map(searchCondition => searchCondition.q)
        }
    })
    if (clauses.length === 1) return clauses[0];
    return { ...q, clauses }
}

interface QObjectProps {
    q: TransformedQObject;
    fulfillments: Fulfillment[]; // fulfillments for this rule 
    unselectedFulfillments: Fulfillment[];
    rule: Rule;
    satisfied: boolean;
    activeDegreePlanId: number;
}
const courseOptions = (codes: string[]): QCourse[] =>
    codes.map((full_code) => ({ type: "COURSE", full_code }));

/** Courses named by a rule, when it names courses and nothing else. */
const onlyNamedCourses = (node: ParsedQObj): QCourse[] | null => {
    if (node.type === "COURSE") return [node];
    if (node.type !== "AND" && node.type !== "OR") return null;
    const found: QCourse[] = [];
    for (const clause of node.clauses) {
        if (clause.type === "LEAF" || clause.type === "SEARCH") return null;
        const child = onlyNamedCourses(clause);
        if (!child) return null;
        found.push(...child);
    }
    return found;
};

const QObject = ({ q, fulfillments, unselectedFulfillments, rule, satisfied, activeDegreePlanId }: QObjectProps) => {
    const panelOptions = useContext(PanelOptionsContext);
    const searchProps = {
        cu: rule.credits,
        num: rule.num,
        fulfillments,
        unselectedFulfillments,
        ruleIsSatisfied: satisfied,
        ruleId: rule.id,
        ruleQuery: rule.q,
        activeDegreeplanId: activeDegreePlanId,
        showCode: !rule.title,
    };

    // recursively render
    switch (q.type) {
        case "OR":
            const courses: QCourse[] = [];
            const coursesWithSemester: QCourse[] = [];
            const searchConditions: Search[] = [];
            q.clauses.forEach(clause => {
                if (clause.type === "COURSE" && clause.semester) coursesWithSemester.push(clause);
                else if (clause.type === "COURSE") courses.push(clause)
                else if (clause.type === "SEARCH") searchConditions.push(clause)
                else throw Error(`Non search or course clause in transformed Q object: ${JSON.stringify(clause)}`);
            })
            const fulfillmentsMap = new Map(fulfillments.map(fulfillment => [fulfillment.full_code, fulfillment]))
            const displayCoursesWithSemesters = coursesWithSemester.map(course => {
                assert(typeof course.semester === "string")
                const fulfillment = fulfillmentsMap.get(course.full_code);
                const isChosen = !!(fulfillment && fulfillment.semester === course.semester);
                const isUnselectedForRule = !isChosen && unselectedFulfillments.some(
                    (unselectedFulfillment) =>
                        unselectedFulfillment.full_code === course.full_code
                        && unselectedFulfillment.semester === course.semester
                );

                // we've already used this course, so delete it 
                if (isChosen) fulfillmentsMap.delete(course.full_code);
                return <CourseInReq course={{ ...course, rules: fulfillment?.rules }} fulfillment={fulfillment} isDisabled={satisfied && !isChosen} isUsed={isChosen} isUnselectedRule={isUnselectedForRule} ruleId={rule.id} activeDegreePlanId={activeDegreePlanId} />;
            });
            const displayCoursesWithoutSemesters = courses.map(course => {
                assert(typeof course.semester === "undefined")
                const fulfillment = fulfillmentsMap.get(course.full_code);
                const isChosen = !!fulfillment;
                const isUnselectedForRule = !isChosen && unselectedFulfillments.some(
                    (unselectedFulfillment) =>
                        unselectedFulfillment.full_code === course.full_code
                );

                // we've already used this course, so delete it
                if (isChosen) fulfillmentsMap.delete(course.full_code);
                return <CourseInReq course={{ ...course, rules: fulfillment?.rules }} fulfillment={fulfillment} isDisabled={satisfied && !isChosen} isUsed={isChosen} isUnselectedRule={isUnselectedForRule} ruleId={rule.id} activeDegreePlanId={activeDegreePlanId} />;
            });

            // transformations applied to parse tree should guarantee that searchConditions is a singleton
            assert(searchConditions.length <= 1, "Expected search conditions to be merged") // TODO!!

            const optionCourses = [...coursesWithSemester, ...courses];
            const panel = panelOptions[String(rule.id)];
            // A filter, or a filter mixed with named courses, is one representation:
            // the matching courses when there are few, otherwise a search with the count.
            if (searchConditions.length > 0) {
                if (panel && panel.courses && panel.courses.length > 0 && panel.count <= SHORT_LIST_MAX) {
                    return <CourseOptionChips options={courseOptions(panel.courses)} fulfillments={fulfillments} />;
                }
                if (panel && panel.count === 0 && optionCourses.length > 0 && optionCourses.length <= SHORT_LIST_MAX) {
                    return <CourseOptionChips options={optionCourses} fulfillments={fulfillments} />;
                }
                return (
                    <SearchCondition
                        {...searchProps}
                        q={searchConditions[0].q}
                        count={panel?.count}
                    />
                );
            }
            if (optionCourses.length > SHORT_LIST_MAX) {
                return (
                    <SearchCondition
                        {...searchProps}
                        q={q}
                        count={optionCourses.length}
                    />
                );
            }
            const courseNodes = optionCourses.length > 1
                ? [<CourseOptionChips key="options" options={optionCourses} fulfillments={fulfillments} />]
                : [...displayCoursesWithSemesters, ...displayCoursesWithoutSemesters];
            return <Row $wrap $gap="4px">
                {interpolate(
                    courseNodes,
                    <CourseOptionsSeparator>or</CourseOptionsSeparator>
                )}
            </Row>
        case "SEARCH":
            const named = onlyNamedCourses(q.q);
            if (named && named.length > 0 && named.length <= SHORT_LIST_MAX) {
                return <CourseOptionChips options={named} fulfillments={fulfillments} />;
            }
            if (named && named.length > SHORT_LIST_MAX) {
                return <SearchCondition {...searchProps} q={q.q} count={named.length} />;
            }
            const searched = panelOptions[String(rule.id)];
            if (searched && searched.courses && searched.courses.length > 0 && searched.count <= SHORT_LIST_MAX) {
                return <CourseOptionChips options={courseOptions(searched.courses)} fulfillments={fulfillments} />;
            }
            return (
                <SearchCondition
                    {...searchProps}
                    q={q.q}
                    count={searched?.count}
                />
            );
        case "COURSE":
            const [fulfillment] = fulfillments.filter(fulfillment => fulfillment.full_code == q.full_code && (!q.semester || q.semester === fulfillment.semester))
            const isUnselectedForRule = !fulfillment && unselectedFulfillments.some(
                (unselectedFulfillment) =>
                    unselectedFulfillment.full_code === q.full_code
                    && (!q.semester || q.semester === unselectedFulfillment.semester)
            );
            return <CourseInReq course={{ ...q, rules: fulfillment ? fulfillment.rules : [] }} fulfillment={fulfillment} isDisabled={satisfied && !fulfillment} isUsed={!!fulfillment} isUnselectedRule={isUnselectedForRule} ruleId={rule.id} activeDegreePlanId={activeDegreePlanId} />;
    }
}

interface RuleLeafProps {
    q_json: any;
    // activeDegreePlanId: number, 
    fulfillmentsForRule: Fulfillment[]; // fulfillments for this rule 
    unselectedFulfillmentsForRule: Fulfillment[];
    rule: Rule;
    satisfied: boolean;
    activeDegreePlanId: number;
    /** The scheduled code is too long to show. The row is a search instead. */
    preferSearch?: boolean;
}

export const SkeletonRuleLeaf = () => (
    <div
        style={{
            display: "flex",
            gap: ".5rem"
        }}
    >
        <SkeletonCourse />
        {/* <CourseOptionsSeparator>or</CourseOptionsSeparator>
        <SkeletonCourse /> 
        <CourseOptionsSeparator>or</CourseOptionsSeparator>
        <SkeletonCourse /> */}
    </div>
)

const RuleLeafWrapper = styled(Row)`
    margin-bottom: 0;
    width: auto;
    flex: 0 1 auto;
    min-width: 0;
`
const RuleLeaf = ({ q_json, fulfillmentsForRule, unselectedFulfillmentsForRule, rule, satisfied, activeDegreePlanId, preferSearch }: RuleLeafProps) => {
    const t1 = transformDepartmentInClauses(q_json);
    const t2 = transformCourseClauses(t1);
    const t3 = transformSearchConditions(t2)
    q_json = t3 as TransformedQObject;

    return (
        <RuleLeafWrapper $wrap $inline $gap="4px">
            {preferSearch ? (
                <SearchCondition
                    cu={rule.credits}
                    num={rule.num}
                    ruleId={rule.id}
                    ruleQuery={rule.q}
                    fulfillments={fulfillmentsForRule}
                    unselectedFulfillments={unselectedFulfillmentsForRule}
                    ruleIsSatisfied={satisfied}
                    q={q_json}
                    activeDegreeplanId={activeDegreePlanId}
                />
            ) : (
                <QObject q={q_json} fulfillments={fulfillmentsForRule} unselectedFulfillments={unselectedFulfillmentsForRule} rule={rule} satisfied={satisfied} activeDegreePlanId={activeDegreePlanId} />
            )}
        </RuleLeafWrapper>
    )
}

export default RuleLeaf;
