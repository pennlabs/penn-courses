import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import type { DnDFulfillment, Fulfillment, Rule } from "@/types";
import styled from "@emotion/styled";
import nearley from "nearley";
import grammar from "@/util/q_object_grammar" 
import { Icon } from "../common/bulma_derived_components";
import { BaseCourseContainer } from "../FourYearPlan/CoursePlanned";
import assert from "assert";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";

const interpolate = <T,>(arr: T[], separator: T) => arr.flatMap(
    (elem, index) => index < arr.length - 1 ? 
    [elem, separator] 
    : [elem]
)


type ConditionKey = "full_code" | "semester" | "attributes__code__in" | "department__code" | "full_code__startswith" | "code__gte" | "code__lte" | "department__code__in" 
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



interface CourseOptionProps {
    full_code: QCourse["full_code"];
    semester?: QCourse["semester"];
    isChosen: boolean;
    ruleIsSatisfied: boolean;
    ruleId: Rule["id"];
}
const CourseOption = ({ full_code, semester, isChosen = false, ruleIsSatisfied = false, ruleId }: CourseOptionProps) => {
    const [{ isDragging }, drag] = useDrag<DnDFulfillment, never, { isDragging: boolean }>(() => ({
        type: ItemTypes.COURSE,
        item: {full_code: full_code, semester: null, rules: [ruleId], course: null },
collect: (monitor) => ({ isDragging: !!monitor.isDragging() }),
        canDrag: !isChosen && !ruleIsSatisfied
    }), [isChosen, ruleIsSatisfied])

    return (
        <ReviewPanelTrigger full_code={full_code}>
            <Draggable isDragging={isDragging}>
                <BaseCourseContainer ref={drag} $isDepressed={isChosen} $isDisabled={!isChosen && ruleIsSatisfied}>
                    {semester ? `${full_code} (${semester})` : full_code.replace("-", " ")}
                </BaseCourseContainer>
            </Draggable>
        </ReviewPanelTrigger>
    )
}

const Row = styled.div`
    display: inline-flex;
    align-items: center;
    display: flex;
    align-content: flex-end;
    gap: .25rem;
    flex-wrap: wrap;
    margin: .5 rem 0;
`;


const Attributes = ({ attributes }: { attributes: string[] }) => {
    return <Row>
        <DarkGrayIcon><i className="fas fa-at fa-sm"></i></DarkGrayIcon> {/*TODO: add a tooltip */}
        <Wrap>{attributes.join(', ')}</Wrap>
    </Row>
}

const SearchConditionWrapper = styled(BaseCourseContainer)`
    display: inline-flex;
    align-items: center;
    align-content: flex-end;
    gap: .25rem;
    flex-wrap: wrap;
    margin: .5 rem 0;
    background-color: #EDF1FC;
    text-wrap: none;

`

const Wrap = styled.span`
    text-wrap: wrap;
`

export const DarkGrayIcon = styled(Icon)`
    color: #575757;
`

interface SearchConditionInnerProps {
    q: ParsedQObj;
}
interface SearchConditionProps extends SearchConditionInnerProps {
    fulfillments: Fulfillment[]
    ruleIsSatisfied: boolean,
    ruleId: Rule["id"];
    setSearchClosed: (status: boolean) => void; // TODO: could remove
    handleSearch: (reqId: number, reqQuery: string) => void;
    ruleQuery: string;
}
const SearchConditionInner = ({ q }: SearchConditionInnerProps) => {
    if (q.type === "LEAF") {
        q = { type: "AND", clauses: [q] }
    } else if (q.type === "COURSE" || q.type === "SEARCH") {
        throw Error("Course inside search condition"); // TODO: this is inelegant
    }

    const conditions = q.clauses.filter((clause) => clause.type === "LEAF") as Condition[];
    const compounds = q.clauses.filter((clause) => clause.type === "OR" || clause.type === "AND") as Compound[];

    const display = [];
    const compoundCondition: Record<ConditionKey, any | undefined> = {};
    conditions.forEach((leaf) => compoundCondition[leaf.key] = leaf.value); 
    if ('attributes__code__in' in compoundCondition) {
        display.push(<Attributes attributes={compoundCondition['attributes__code__in'] as string[]} />);
    }
    if ('department__code' in compoundCondition && 'code__gte' in compoundCondition && 'code__lte' in compoundCondition) {
        display.push(<Wrap>{compoundCondition['department__code']} {compoundCondition['code__gte']}-{compoundCondition['code__lte']}</Wrap>);
    } else if ('department__code' in compoundCondition && 'code__gte' in compoundCondition) {
        display.push(<Wrap>{compoundCondition['department__code']} {compoundCondition['code__gte']}-9999</Wrap>);
    } else if ('department__code' in compoundCondition && 'code__lte' in compoundCondition) {
        display.push(<Wrap>{compoundCondition['department__code']} 0000-{compoundCondition['code__lte']}</Wrap>);
    } else if ('department__code' in compoundCondition) {
        display.push(<Wtsp>in {compoundCondition['department__code']}</Wtsp>);
    } else if ('code__lte' in compoundCondition && 'code__gte' in compoundCondition) {
        display.push(<div>course number {compoundCondition['code__lte']}-{compoundCondition['code__gte']}</div>);
    } else if ('code__lte' in compoundCondition) {
        display.push(<div>course number &lt;= {compoundCondition['code__lte']}</div>);
    } else if ('code__gte' in compoundCondition) {
        display.push(<div>course number &gt;= {compoundCondition['code__gte']}</div>);
    }
    if ('department__code__in' in compoundCondition) {
        const departments = compoundCondition['department__code__in'] as string[];
        display.push(<Row> in {
            interpolate(departments.map((dept) => <div key={dept}>{dept}</div>), <CourseOptionsSeparator>or</CourseOptionsSeparator>)
        }</Row>);
    }
    if ('full_code__startswith' in compoundCondition) {
        const padding = "XXXX-XXXX";
        display.push(<div>{compoundCondition['full_code__startswith']}{padding.slice((compoundCondition['full_code__startswith'] as string).length)}</div>);
    }
    if ("semester" in compoundCondition) {
        display.push(<div>{compoundCondition['semester']}</div>);
    }

    compounds.forEach((compound) => display.push(
        <Row>
            <CourseOptionsSeparator>{'('}</CourseOptionsSeparator>
            <SearchConditionInner q={compound} />
            <CourseOptionsSeparator>{')'}</CourseOptionsSeparator>
        </Row>
    ));

    if (display.length == 0) {
        console.error("Empty display in SearchCondition: ", q)
    }

    return (
        <>
            {interpolate(display, <CourseOptionsSeparator>{q.type}</CourseOptionsSeparator>)}
        </>
    )
}

const SearchCondition = ({handleSearch, ruleId, ruleQuery, fulfillments, ruleIsSatisfied, q}: SearchConditionProps) => (
    <SearchConditionWrapper $isDisabled={ruleIsSatisfied}>
        <SearchConditionInner q={q} />
        <div onClick={() => {handleSearch(ruleId, ruleQuery);}}>
            <DarkGrayIcon>
                <i className="fas fa-search fa-sm"></i>
            </DarkGrayIcon>
        </div>
        {fulfillments.map(fulfillment => (
            <CourseOption 
            full_code={fulfillment.full_code} 
            isChosen 
            ruleIsSatisfied={ruleIsSatisfied} 
            ruleId={ruleId}
            />
        ))}
    </SearchConditionWrapper>
)

const CourseOptionsSeparator = styled.span`
    font-size: .8rem;
    text-transform: uppercase;
    color: #575757;
    font-weight: 500;
`;

const transformCourseClauses = (q: ParsedQObj): ParsedQObj => {
    if (q.type === "LEAF" && q.key === "full_code") return { type: "COURSE", full_code: q.value };
    if (q.type === "AND" && q.clauses.length == 2) {
        const semester = (q.clauses.find((clause) => clause.type === "LEAF" && clause.key === "semester") as Condition | undefined)?.value as string | undefined;
        const full_code = (q.clauses.find((clause) => clause.type === "LEAF" && clause.key === "full_code") as Condition | undefined)?.value as string | undefined;
        if (full_code) return { type: "COURSE", semester, full_code };
    }
    // parse recursively
    if (q.type === "AND" || q.type === "OR") return {...q, clauses: q.clauses.map(transformCourseClauses)}
    return q;
}
const transformDepartmentInClauses = (q: ParsedQObj): ParsedQObj => {
    if (q.type === "LEAF" && q.key === "department__code__in") return {
        type: "OR", 
        clauses: (q.value as string[]).map(dept => ({ type: "LEAF", key: "department__code", value: dept })) 
    }; 
    if (q.type === "AND" || q.type === "OR") return {...q, clauses: q.clauses.map(transformDepartmentInClauses)}
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
    return {...q, clauses }
}

interface QObjectProps { 
    q: TransformedQObject; 
    fulfillments: Fulfillment[]; // fulfillments for this rule 
    rule: Rule;
    satisfied: boolean;
    handleSearch: (ruleId: Rule["id"], ruleQuery: Rule["q"]) => void;
}
const QObject = ({ q, fulfillments, rule, satisfied, handleSearch }: QObjectProps) => {
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
                
                // we've already used this course, so delete it 
                if (isChosen) fulfillmentsMap.delete(course.full_code);
                return <CourseOption full_code={course.full_code} semester={course.semester} isChosen={isChosen} ruleIsSatisfied={satisfied} ruleId={rule.id} />;
            });
            const displayCoursesWithoutSemesters = courses.map(course => {
                assert(typeof course.semester === "undefined")
                const fulfillment = fulfillmentsMap.get(course.full_code);
                const isChosen = !!fulfillment;

                // we've already used this course, so delete it
                if (isChosen) fulfillmentsMap.delete(course.full_code); 
                return <CourseOption full_code={course.full_code} isChosen={isChosen} ruleIsSatisfied={satisfied} ruleId={rule.id} />;
            });

            // transformations applied to parse tree should guarantee that searchConditions is a singleton
            assert(searchConditions.length <= 1, "Expected search conditions to be merged")
            const displaySearchConditions = searchConditions.map(search => {
                const courses = Array.from(fulfillmentsMap.values())
                fulfillmentsMap.clear()
                return <SearchCondition fulfillments={courses} q={search.q} ruleIsSatisfied={satisfied} ruleId={rule.id} ruleQuery={rule.q} handleSearch={handleSearch}/>
            })

            return <Row>{
                interpolate(
                    [...displayCoursesWithSemesters, ...displayCoursesWithoutSemesters, ...displaySearchConditions], 
                    <CourseOptionsSeparator>or</CourseOptionsSeparator>
                )}</Row>
        case "SEARCH":
            return <SearchCondition q={q.q} ruleIsSatisfied={satisfied} fulfillments={fulfillments} ruleId={rule.id} ruleQuery={rule.q} />;
        case "COURSE":
            const isChosen = !!fulfillments.find(fulfillment => fulfillment.full_code == q.full_code && (!q.semester || q.semester === fulfillment.semester))
            return <CourseOption full_code={q.full_code} semester={q.semester} isChosen={isChosen} ruleIsSatisfied={satisfied} ruleId={rule.id} />
    }
}


interface RuleLeafProps { 
    q: string;
    fulfillmentsForRule: Fulfillment[]; // fulfillments for this rule 
    rule: Rule;
    satisfied: boolean;
    handleSearch: (ruleId: Rule["id"], ruleQuery: Rule["q"]) => void;
}
const RuleLeaf = ({ q, fulfillmentsForRule, rule, satisfied, handleSearch }: RuleLeafProps) => {
    const qObjParser = new nearley.Parser(nearley.Grammar.fromCompiled(grammar));
    let parsed = qObjParser.feed(q).results[0] as ParsedQObj;
    if (!parsed) return null;

    // apply some transformations to parse tree
    const t1 = transformDepartmentInClauses(parsed);
    const t2 = transformCourseClauses(t1);
    const t3 = transformSearchConditions(t2)
    parsed = t3 as TransformedQObject;
    return <QObject q={parsed} fulfillments={fulfillmentsForRule} rule={rule} satisfied={satisfied} handleSearch={handleSearch}/>
}

export default RuleLeaf;