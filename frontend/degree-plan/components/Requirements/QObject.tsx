import CoursePlanned, { BaseCourseContainer } from "../FourYearPlan/CoursePlanned";
import CourseComp from "./Course";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { useEffect, useState } from "react";
import type { Course } from "@/types";
import styled from "@emotion/styled";
import nearley from "nearley";
import grammar from "@/util/q_object_grammar" 

interface Condition {
    type: 'LEAF';
    key: string;
    value: string | number | boolean | null | string[];
}
interface Compound {
    type: 'OR' | 'AND';
    clauses: (Compound | Condition)[];
}
type ParsedQObj = Condition | Compound;

interface CourseOptionsProps {
    course: Course["full_code"];
    chosenOption: Course["full_code"] | null;
    setChosenOption: (arg0: Course["full_code"] | null) => void;
}
const CourseOption = ({ course, chosenOption, setChosenOption }: CourseOptionsProps) => {
    const [{ isDragging }, drag] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: {id: course}, semester:-1},
        end: (item, monitor) => {
            if (monitor.didDrop()) setChosenOption(course);
        },
        collect: (monitor) => ({ isDragging: !!monitor.isDragging() }),
        canDrag: () => !chosenOption // if another hasn't already been chosen
    }))

    return (
        <BaseCourseContainer ref={drag}>
            {course}
        </BaseCourseContainer>
    )
}

const CourseOptionsContainer = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    text-wrap: nowrap;
    gap: .5em;
    border-radius: 5px;

`;

const CourseOptionsSeparator = styled.div`
    font-size: .8rem;
    text-transform: uppercase;
    color: #575757;
    font-weight: 500;
`;

const CourseOptions = ({ courses }: { courses: Course["full_code"][]}) => {
    const [chosenOption, setChosenOption] = useState<Course["full_code"] | null>(null);
    const options = courses
        .map((course) => <CourseOption chosenOption={chosenOption} setChosenOption={setChosenOption} course={course} />)
        .flatMap((elem, index) => (
            index < courses.length - 1 ? 
            [elem, <CourseOptionsSeparator>or</CourseOptionsSeparator>] : 
            [elem])
        );
    
    return (
        <CourseOptionsContainer>
            {options}
        </CourseOptionsContainer>
    );
}

const CourseSearch = ({ QObject }: { QObject: ParsedQObj }) => {
    // search for the course

    // get the string representation
    return <div>
        {JSON.stringify(QObject)}
    </div>
}

const QObject = ({ qObject }: { qObject: string }) => {
    const qObjParser = new nearley.Parser(nearley.Grammar.fromCompiled(grammar));
    const parsed = qObjParser.feed(qObject).results[0] as ParsedQObj;
    if (!parsed) return null;
    // case 1: leaf full code
    if (parsed.type === 'LEAF' && parsed.key === "full_code") return <CourseOptions courses={[parsed.value]} />;
    if (
        parsed.type === "OR" &&
        parsed.clauses.length <= 5 &&
        parsed.clauses.every((clause) => clause.type === "LEAF" && clause.key === "full_code") 
    ) return <CourseOptions courses={(parsed.clauses as Condition[]).map((leaf) => leaf.value)} />;
    return <CourseSearch QObject={parsed} />;
}

export default QObject;