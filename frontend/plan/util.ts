import { AdvancedSearchBoolean, AdvancedSearchData, AdvancedSearchEnum, AdvancedSearchNumeric, AdvancedSearchValue, FilterData } from "./types";

function decimalToTimeString(decimalTime: number): number {
    const hour = Math.floor(decimalTime);
    const mins = parseFloat(((decimalTime % 1) * 0.6).toFixed(2));
    return Math.min(23.59, hour + mins);
}

export function buildCourseSearchRequest(filterData: FilterData): AdvancedSearchData {
    const children = []

    const numerics = ["difficulty", "course_quality", "instructor_quality"];
    for (const field of numerics) {
        const [lb, ub] = filterData[field as keyof FilterData] as [number, number];
        if (lb !== 0) {
            children.push({
                type: "numeric",
                field: field,
                op: "gte",
                value: lb,
            } as AdvancedSearchNumeric);
        }

        if (ub !== 4) {
            children.push({
                type: "numeric",
                field: field,
                op: "lte",
                value: ub,
            } as AdvancedSearchNumeric);
        }
    }

    const startTime = decimalToTimeString(24 - filterData.time[1]);
    const endTime = decimalToTimeString(24 - filterData.time[0]);
    if (startTime !== 7) {
        children.push({
            type: "numeric",
            field: "start_time",
            op: "gte",
            value: startTime,
        } as AdvancedSearchNumeric);
    }
    if (endTime !== 22.3) {
        children.push({
            type: "numeric",
            field: "end_time",
            op: "lte",
            value: endTime,
        } as AdvancedSearchNumeric);
    }

    const enums = [["cu", 3], ["activity", 4], ["days", 7]] as [keyof FilterData, number][];
    for (const [field, defaultLen] of enums) {
        const selections = 
            Object.entries(filterData[field])
                .filter(([_, isSelected]) => isSelected)
                .map(([key]) => key.toUpperCase());
            if (selections.length < defaultLen && selections.length > 0) {
                children.push({
                    type: "enum",
                    field: field,
                    op: "is_any_of",
                    value: selections,
                } as AdvancedSearchEnum);
            }
    }

    if (typeof filterData["schedule-fit"] === 'number' && filterData["schedule-fit"] >= 0) {
        children.push({
            type: "value",
            field: "fit_schedule",
            value: filterData["schedule-fit"],
        } as AdvancedSearchValue);
    }

    if (filterData["is_open"] === 1) {
        children.push({
            type: "boolean",
            field: "is_open",
            value: true,
        } as AdvancedSearchBoolean);
    }

    return {
        query: filterData.searchString,
        filters: {
            op: "AND",
            children: children,
        }
    }
}