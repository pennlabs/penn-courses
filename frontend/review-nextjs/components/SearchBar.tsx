"use client";

import { useDebouncedState } from "@/hooks/debounce";
import { fetchQuery } from "@/lib/search";
import { SearchResult } from "@/lib/types";
import { cn, fetchDummyResults } from "@/lib/utils";
import { redirect } from "next/navigation";
import { useEffect, useState } from "react";

enum SearchStatus {
    IDLE,
    LOADING,
    SUCCESS,
    ERROR,
}

export default function SearchBar() {
    const [query, setQuery] = useState("");
    const [debouncedQuery, setDebouncedQuery] = useDebouncedState("");
    const [results, setResults] = useState<SearchResult | null>(null);
    const [status, setStatus] = useState(SearchStatus.IDLE);

    useEffect(() => {
        if (!debouncedQuery) {
            setResults(null);
            return;
        }
        setStatus(SearchStatus.LOADING);
        fetchDummyResults(debouncedQuery)
            .then((res) => {
                setResults(res);
                setStatus(SearchStatus.SUCCESS);
            })
            .catch((e) => {
                console.error(e);
                setStatus(SearchStatus.ERROR);
            })
            .finally(() => {
                setStatus(SearchStatus.IDLE);
            });
    }, [debouncedQuery]);

    const handleKeyDown = async (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            redirect("/review");
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(e.target.value);
        setDebouncedQuery(e.target.value);
    };

    return (
        <div className={cn("flex", "flex-col", "w-[600px]")}>
            <input
                className={cn(
                    "bg-white",
                    "shadow-xl",
                    "p-3",
                    "border",
                    "min-w-fit",
                    "border-[#f3f3f3]",
                    "text-3xl"
                )}
                type="text"
                value={query}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                placeholder="Search for a class or professor..."
            />
            <p>{debouncedQuery}</p>
            <p>{status}</p>
            <p>{results?.Departments[0]?.name}</p>
        </div>
    );
}
