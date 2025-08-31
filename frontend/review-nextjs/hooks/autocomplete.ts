import { useEffect, useMemo, useState } from "react";
import Fuse from "fuse.js";
import {
    AutocompleteData,
    AutocompleteObject,
    AutocompleteResult,
} from "@/lib/types";
import { apiFetch } from "@/lib/api";
import { useDebouncedState } from "./debounce";

type Indices = {
    courses: Fuse<AutocompleteObject>;
    instrs: Fuse<AutocompleteObject>;
    depts: Fuse<AutocompleteObject>;
};

export function useAutocomplete(): [
    AutocompleteResult | null,
    (query: string) => void
] {
    const [indices, setIndices] = useState<Indices | null>(null);
    const [debouncedQuery, setDebouncedQuery] = useDebouncedState("");

    useEffect(() => {
        async function fetchData() {
            try {
                const response = await apiFetch("/api/review/autocomplete");
                const data: AutocompleteData = await response.json();
                const ops = {
                    threshold: 0.3,
                    keys: ["title", "desc"],
                };
                setIndices({
                    courses: new Fuse<AutocompleteObject>(data.courses, ops),
                    instrs: new Fuse<AutocompleteObject>(data.instructors, ops),
                    depts: new Fuse<AutocompleteObject>(data.departments, ops),
                });
            } catch (e) {
                console.error(e);
            }
        }

        fetchData();
    }, []);

    const results = useMemo(
        () =>
            debouncedQuery.trim() && indices
                ? {
                      courses: indices.courses.search(debouncedQuery, { limit: 25 }),
                      departments: indices.depts.search(debouncedQuery, { limit: 10 }),
                      instructors: indices.instrs.search(debouncedQuery, { limit: 25 }),
                  }
                : null,
        [debouncedQuery]
    );

    return [results, setDebouncedQuery];
}
