"use client";

import { useDebouncedState } from "@/hooks/debounce";
import { fetchQuery } from "@/lib/search";
import { SearchResult } from "@/lib/types";
import { cn, fetchDummyResults } from "@/lib/utils";
import { redirect } from "next/navigation";
import { useEffect, useState } from "react";
import {
    Command,
    CommandDialog,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
    CommandSeparator,
    CommandShortcut,
} from "@/components/ui/command";

enum SearchStatus {
    IDLE,
    LOADING,
    SUCCESS,
    ERROR,
}

export default function SearchBar({ small }: { small?: boolean }) {
    const [query, debouncedQuery, setQuery] = useDebouncedState("");
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

    return (
        <div className={cn("flex", "flex-col", "w-[600px]")}>
            <Command shouldFilter={false}>
                <CommandInput
                    placeholder="Search for a class or professor..."
                    value={query}
                    onValueChange={setQuery}
                />
                <CommandList>
                    {results?.Courses.length && (
                        <CommandGroup heading="Courses">
                            {results.Courses.map((course) => (
                                <CommandItem
                                    key={course.code}
                                    onSelect={() => {
                                        redirect(`/review`);
                                    }}
                                >
                                    {course.code} - {course.title}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                    {results?.Departments.length && (
                        <CommandGroup heading="Departments">
                            {results.Departments.map((dept) => (
                                <CommandItem
                                    key={dept.code}
                                    onSelect={() => {
                                        redirect(`/review`);
                                    }}
                                >
                                    {dept.code} - {dept.name}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                    {results?.Instructors.length && (
                        <CommandGroup heading="Instructors">
                            {results.Instructors.map((ins) => (
                                <CommandItem
                                    key={ins.name}
                                    onSelect={() => {
                                        redirect(`/review`);
                                    }}
                                >
                                    {ins.name} - {ins.id}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                </CommandList>
            </Command>
            {/* <input
                className={cn(
                    small ? "bg-gray-100" : "bg-white",
                    small ? "text-xs" : "text-3xl",
                    small && "rounded-full",
                    small || "shadow-xl",
                    small || "border",
                    small || "border-[#f3f3f3]",
                    "min-w-fit",
                    "outline-hidden",
                    "mx-3",
                    "p-3"
                )}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && redirect("/review")}
                placeholder="Search for a class or professor..."
            /> */}
        </div>
    );
}
