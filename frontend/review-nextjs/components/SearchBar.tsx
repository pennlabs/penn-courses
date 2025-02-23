"use client";

import { cn } from "@/lib/utils";
import { redirect } from "next/navigation";
import { useEffect, useState } from "react";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import { useAutocomplete } from "@/hooks/autocomplete";

enum SearchStatus {
    IDLE,
    LOADING,
    SUCCESS,
    ERROR,
}

export default function SearchBar({ small }: { small?: boolean }) {
    const [query, setQuery] = useState("");
    const [results, sendQuery] = useAutocomplete();
    const [status, setStatus] = useState(SearchStatus.IDLE);

    useEffect(() => {
        sendQuery(query);
        setStatus(SearchStatus.SUCCESS);
    }, [query]);

    return (
        <div className={cn("flex", "flex-col", "w-[600px]")}>
            <Command shouldFilter={false}>
                <CommandInput
                    placeholder="Search for a class or professor..."
                    value={query}
                    onValueChange={setQuery}
                />
                <CommandList>
                    {results &&
                        results.courses.length === 0 &&
                        results.departments.length === 0 &&
                        results.instructors.length === 0 && (
                            <CommandEmpty>No results found</CommandEmpty>
                        )}
                    {results && results.departments.length > 0 && (
                        <CommandGroup heading="Departments">
                            {results?.departments.map((dept) => (
                                <CommandItem
                                    key={dept.item.title}
                                    onSelect={() => {
                                        redirect(`/review${dept.item.url}`);
                                    }}
                                >
                                    {dept.item.title} - {dept.item.desc}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                    {results && results.courses.length > 0 && (
                        <CommandGroup heading="Courses">
                            {results?.courses.map((course) => (
                                <CommandItem
                                    key={course.item.title}
                                    onSelect={() => {
                                        redirect(`/review${course.item.url}`);
                                    }}
                                >
                                    {course.item.title} - {course.item.desc}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                    {results && results.instructors.length > 0 && (
                        <CommandGroup heading="Instructors">
                            {results?.instructors.map((ins) => (
                                <CommandItem
                                    key={ins.item.title}
                                    onSelect={() => {
                                        redirect(`/review${ins.item.url}`);
                                    }}
                                >
                                    {ins.item.title} - {ins.item.desc}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                </CommandList>
            </Command>
        </div>
    );
}
