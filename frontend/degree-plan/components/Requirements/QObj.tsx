// <Q: (OR: (AND: ('code__gte', 0), ('code__lte', 4999), ('department__code', '@'), ('attributes__code__in', ['APPF'])), (AND: ('code__gte', 5000), ('code__lte', 9999), ('department__code', '@'), ('attributes__code__in', ['APPF'])))>

import axios from "../services/httpServices";
import CoursePlanned from "../FourYearPlan/CoursePlanned";
import Course from "./Course";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { useEffect, useState } from "react";

const termChar = '>';

let levels = [];

export const trimQuery = (query: string) => {
    let startIdx = 0;
    let endIdx = query.length - 1;
    while (query[startIdx] !== '(') startIdx++;
    while (query[endIdx] !== ')') endIdx--;
    return query.substring(startIdx, endIdx + 1);
}

const splitQuery = (query: string) => {
    let idx = 0;
    let count = 0;
    let clause = "";
    let clauses = [];
    while (idx < query.length) {
        if (query[idx] === '(') count++;
        if (query[idx] === ')') count--;
        clause += query[idx];
        if (idx != 0 && count == 0) { // if the number of '(' and ')' balance out, we have reached the end of a clause
            clauses = [...clauses, clause];
            clause = ""; // reset for the next clause;
            while (idx < query.length && query[idx] !== '(') idx++; // fast forward to the next '('
        } else {
            idx++;
        }
    }
    return clauses;
}

const checkValidLeafQObj = (query: string) => {
    let count = 0;
    let idx = 0;
    while (idx < query.length) {
        if (query[idx++] === ',') count++;
    }
    return query[0] === '(' &&
            query.endsWith(')') &&
            count == 1;
}

const stripChar = (str: string, start, end?) => {
    if (str[0] === start) str = str.slice(1);
    if (str.endsWith(end ? end: start)) str = str.slice(0, str.length - 1);
    return str;
}

/** This is a recursive component */
const RootQObj = ({query, reqId}) => {
    /** TODO: This needs to be from parent element and from a single source of truth */
    const [satisfiedByIds, setSatisfiedByIds] = useState([]);

    /* OR clause */
    if (query.substring(0, 5) === '(OR: ') {
        return (
            <div className="">
                {splitQuery(stripChar(query, '(', ')').slice(4)).map((clause, i) => (
                    <>
                        {i !== 0 && <div>OR</div>}
                        <RootQObj query={clause} reqId={reqId}/>
                    </>
                ))}
            </div>);
    } 
    /* AND clause */
    else if (query.substring(0, 6) === '(AND: ') {
        return (
            <div className="">
                {splitQuery(stripChar(query, '(', ')').slice(5)).map(clause => (
                    <div className="d-flex">
                        <div style={{backgroundColor:'green', width: '5px', marginRight: '5px'}}></div>
                        <RootQObj query={clause} reqId={reqId}/>
                    </div>
                ))}
            </div>);
    }

    /* Base case: Leaf clause */
    if (checkValidLeafQObj(query)) {
        let [key, value] = query.substring(1, query.length - 1).split(', ');
        let queryComponent;
        switch (stripChar(key, '\'')) {
            case 'full_code':
                const courseId = `${stripChar(value, '\'')}`;
                const [{ isDragging }, drag] = useDrag(() => ({
                    type: ItemTypes.COURSE,
                    item: {course: {id: courseId, satisfyIds:[reqId]}, semester:-1},
                    end(item, monitor) {
                        if (monitor.didDrop()) {
                            setSatisfiedByIds([...satisfiedByIds, courseId]);
                        }
                    },
                    collect: (monitor) => ({
                        isDragging: !!monitor.isDragging(),
                    })
                }))
                queryComponent = 
                    <div style={{backgroundColor: '#DBE2F5', borderRadius: '5px', padding: '3px'}} ref={drag}>
                        {courseId}
                    </div>
                break;
            case 'code__gte':
                queryComponent = `course code is greater than or equal to ${value}`;
                break;
            case 'code__lte':
                queryComponent = `course code is less than or equal to ${value}`;
                break;
            case 'semester__code':
                queryComponent = `must be from ${value} semester`;
                break;
            case 'department__code':
                queryComponent = `must be listed under ${value} department`;
                break;
            case 'attributes__code__in':
                const attrs = stripChar(value, '[', ']');
                queryComponent = `attribute must be one of`;
                // for (const attr in attrs) {
                    queryComponent += stripChar(attrs, '\'');
                // }
                break;
            default:
                queryComponent = `${key}: ${value}`;
                break;
        }
        //style={{backgroundColor: satisfiedByIds.length > 0 ? 'green' : 'grey'}} className="p-3"
        return (<div >
            {queryComponent}
        </div>)
    }
    
    /* Base case: leaf clause or uncovered cases */
    return (<div >{query}</div>);

}

export default RootQObj;