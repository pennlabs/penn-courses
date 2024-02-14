import CoursePlanned, { BaseCourseContainer } from "../FourYearPlan/CoursePlanned";
import CourseComp from "./Course";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { useEffect, useState } from "react";
import type { Course } from "@/types";
import styled from "@emotion/styled";
import nearley from "nearley";
import grammar from "@/util/q_object_grammar" 
import { Icon } from "../bulma_derived_components";
import assert from "assert";

type ConditionKey = "full_code" | "semester" | "attributes__code__in" | "department__code" | "full_code__startswith" | "code__gte" | "code__lte" | "department__code__in" 
interface Condition {
    type: 'LEAF';
    key: ConditionKey;
    value: string | number | boolean | null | string[];
}
interface Compound {
    type: 'OR' | 'AND';
    clauses: (Compound | Condition)[];
}
type ParsedQObj = Condition | Compound;

interface CourseOptionProps {
    course: Course["full_code"];
    chosenOptions: Course["full_code"][];
    setChosenOptions: (arg0: Course["full_code"][]) => void;
    semester?: Course["semester"];
}
const CourseOption = ({ course, chosenOptions, setChosenOptions, semester }: CourseOptionProps) => {
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: {id: course}, semester:-1},
        end: (item, monitor) => {
            if (monitor.didDrop()) setChosenOptions(course);
        },
        collect: (monitor) => ({ isDragging: !!monitor.isDragging() }),
        canDrag: () => !chosenOptions.length // if another hasn't already been chosen
    }))

    return (
        <BaseCourseContainer ref={drag}>
            {course.split("-").join(" ")}{semester ? ` (${semester})` : ""}
        </BaseCourseContainer>
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
        <DarkGrayIcon><i class="fas fa-at fa-sm"></i></DarkGrayIcon> {/*TODO: add a tooltip */}
        <div>{attributes.join(', ')}</div>
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
`
const DarkGrayIcon = styled(Icon)`
    color: #575757;
`

interface SearchConditionProps {
    compound: Compound;
    chosenOptions: Course["full_code"][];
    setChosenOptions: (arg0: Course["full_code"][]) => void;
}
const SearchCondition = ({ compound, chosenOptions, setChosenOptions }: SearchConditionProps) => {
    const conditions = compound.clauses.filter((clause) => clause.type === "LEAF") as Condition[];
    const compounds = compound.clauses.filter((clause) => clause.type !== "LEAF") as Compound[];

    const display = [];
    const compoundCondition: { [key: ConditionKey]: any } = {};
    conditions.forEach((leaf) => compoundCondition[leaf.key] = leaf.value); 
    if ('attributes__code__in' in compoundCondition) {
        display.push(<Attributes attributes={compoundCondition['attributes__code__in'] as string[]} />);
    }
    if ('department__code' in compoundCondition && 'code__gte' in compoundCondition && 'code__lte' in compoundCondition) {
        display.push(<div>{compoundCondition['department__code']} {compoundCondition['code__gte']} - {compoundCondition['code__lte']}</div>);
    } else if ('department__code' in compoundCondition && 'code__gte' in compoundCondition) {
        display.push(<div>{compoundCondition['department__code']} {compoundCondition['code__gte']}-9999</div>);
    } else if ('department__code' in compoundCondition && 'code__lte' in compoundCondition) {
        display.push(<div>{compoundCondition['department__code']} 0000-{compoundCondition['code__lte']}</div>);
    } else if ('department__code' in compoundCondition) {
        display.push(<div>in {compoundCondition['department__code']}</div>);
    } else if ('code__lte' in compoundCondition && 'code__gte' in compoundCondition) {
        display.push(<div>course number {compoundCondition['code__lte']}-{compoundCondition['code__gte']}</div>);
    } else if ('code__lte' in compoundCondition) {
        display.push(<div>course number &lt;= {compoundCondition['code__lte']}</div>);
    } else if ('code__gte' in compoundCondition) {
        display.push(<div>course number &gt;= {compoundCondition['code__gte']}</div>);
    }
    if ('department__code__in' in compoundCondition) {
        const departments = compoundCondition['department__code__in'] as string[];
        display.push(<Row>in {
            departments.map((dept) => <div>{dept}</div>)
            .flatMap((elem, index) => index < departments.length - 1 ? [elem, <CourseOptionsSeparator>or</CourseOptionsSeparator>] : [elem])
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
            <CourseOptionsSeparator id="parens">{'('}asnd</CourseOptionsSeparator>
            <SearchCondition compound={compound} />
            <CourseOptionsSeparator>{')'}asdf</CourseOptionsSeparator>
        </Row>
    ));

    if (display.length == 0) {
        console.error("Empty display in SearchCondition: ", compound)
    }

    return (
        <SearchConditionWrapper>
            {display.flatMap(
                (elem, index) => index < display.length - 1 ? 
                    [elem, <CourseOptionsSeparator>and</CourseOptionsSeparator>] 
                    : [elem]
            )}
            <DarkGrayIcon>
                <i class="fas fa-search fa-sm"></i>
            </DarkGrayIcon>
        </SearchConditionWrapper>
    )
}

interface TerminalProps {
    q: ParsedQObj;
    chosenOptions: Course["full_code"][];
    setChosenOptions: (arg0: Course["full_code"][]) => void;
}
const Terminal = ({ q, chosenOptions, setChosenOptions }: TerminalProps) => {
    assert(q.type !== "OR");
    if (q.type === 'LEAF' && q.key === "full_code") return (
        <CourseOption course={q.value as string} chosenOptions={chosenOptions} setChosenOptions={setChosenOptions} />
    );
    if (q.type === 'LEAF') return (
        <SearchCondition compound={{type: "AND", clauses: [q]}} chosenOptions={chosenOptions} setChosenOptions={setChosenOptions} />
    );
    if (q.type === 'AND' && q.clauses.length == 2) {
        const semester = q.clauses.find((clause) => clause.type === "LEAF" && clause.key === "semester")
        const full_code = q.clauses.find((clause) => clause.type === "LEAF" && clause.key === "full_code")
        if (semester && full_code) return (
            <CourseOption 
            course={(full_code as Condition).value as string} 
            semester={(semester as Condition).value as string} 
            chosenOptions={chosenOptions}
            setChosenOptions={setChosenOptions}
            />
        );
    }
    return  <SearchCondition compound={q} />;
}

const CourseOptionsSeparator = styled.div`
    font-size: .8rem;
    text-transform: uppercase;
    color: #575757;
    font-weight: 500;
`;

const QObject = ({ q }: { q: string }) => {
    console.log(q);
    const qObjParser = new nearley.Parser(nearley.Grammar.fromCompiled(grammar));
    let parsed = qObjParser.feed(q).results[0] as ParsedQObj;
    const [chosenOptions, setChosenOptions] = useState<Course["full_code"][]>([]);
    if (!parsed) return null;
    if (parsed.type == "OR" && parsed.clauses.every((clause) => clause.type === "LEAF" && clause.key === "department__code")) {
        parsed = {type: "LEAF", key: "department__code__in", value: parsed.clauses.map((clause) => (clause as Condition).value) as string[]} as Condition;
    }
    if (parsed.type == "OR") {
        return (
            <Row>
                {parsed.clauses
                .map((clause) => <Terminal q={clause} chosenOptions={chosenOptions} setChosenOptions={setChosenOptions}/>)
                .flatMap((elem, index) => (
                    index < parsed.clauses.length - 1 ? 
                    [elem, <CourseOptionsSeparator>or</CourseOptionsSeparator>] : 
                    [elem]
                ))}
            </Row>
        )
    }
    return (
        <Terminal 
        q={parsed}
        chosenOptions={chosenOptions}
        setChosenOptions={setChosenOptions}  
        />
    )
}

export default QObject;