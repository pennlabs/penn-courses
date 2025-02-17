import { SearchOptions, SearchResult } from "./types";
export const PCS_API_DOMAIN = "https://penn-course-search-fly.fly.dev";

export const normalizeQuery = (query: string) => {
    query = query.replaceAll("-", " ");
    query = query.replaceAll(/[–—…«»‘’]/g, " ");
    query = query.replaceAll(/[“”]/g, '"');
    if (query.length >= 2 && query.slice(-2).match(/\w{2}/)) {
        const i = /\w+$/.exec(query)!.index;
        const partial = query.substring(i);
        query = query.substring(0, i) + `(${partial}|${partial}*|%${partial}%)`;
    } else if (query.length == 1) {
        query = `(${query}|${query}*)`;
    } else if (query.length >= 1 && query.slice(-1).match(/\w/)) {
        query = query.slice(0, -1);
    }
    return query;
};

export const fetchQuery = async (
    query: string,
    options: SearchOptions = {
        workLow: 0,
        workHigh: 4,
        difficultyLow: 0,
        difficultyHigh: 4,
        qualityLow: 0,
        qualityHigh: 4,
    }
): Promise<SearchResult> => {
    console.log("hi");
    const normalizedQuery = normalizeQuery(query);
    const urlParams = new URLSearchParams(
        Object.entries(options).map(([k, v]) => [k, v.toString()])
    );
    const res = await fetch(
        `${PCS_API_DOMAIN}/search?q=${encodeURIComponent(
            normalizedQuery
        )}&${urlParams.toString()}`
    );

    return await res.json();
};
