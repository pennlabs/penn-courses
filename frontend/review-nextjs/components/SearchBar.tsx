"use client";

import { cn } from "@/lib/utils";
import { redirect } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import { useAutocomplete } from "@/hooks/autocomplete";

export default function SearchBar({ header }: { header?: boolean }) {
    const [query, setQuery] = useState("");
    const [results, sendQuery] = useAutocomplete();
    const [isOpen, setIsOpen] = useState(false);
    const commandRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        sendQuery(query);
    }, [query]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (commandRef.current && !commandRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    return (
        <div className={cn("flex", "flex-col", "w-[600px]", header && "ml-3")}>
            <Command
                ref={commandRef}
                shouldFilter={false}
                className={cn("h-[36px]", header && "bg-background")}
            >
                <CommandInput
                    placeholder="Search for a class or professor..."
                    value={query}
                    onValueChange={(value) => {
                        setQuery(value);
                        setIsOpen(value.length > 0);
                    }}
                    className={cn("h-[36px]", header && "bg-background")}
                />
                <CommandList>
                    {results && isOpen &&
                        results.courses.length === 0 &&
                        results.departments.length === 0 &&
                        results.instructors.length === 0 && (
                            <CommandEmpty>No results found</CommandEmpty>
                        )}
                    {results && isOpen && results.departments.length > 0 && (
                        <CommandGroup heading="Departments">
                            {results?.departments.map((dept) => (
                                <CommandItem
                                    key={dept.item.url}
                                    // onSelect={handleSelect(dept.item.url)}
                                    onSelect={() => {
                                        setIsOpen(false);
                                        redirect(`/review${dept.item.url}`);
                                    }}
                                >
                                    {dept.item.title} - {dept.item.desc}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                    {results && isOpen && results.courses.length > 0 && (
                        <CommandGroup heading="Courses">
                            {results?.courses.map((course) => (
                                <CommandItem
                                    key={course.item.url}
                                    // onSelect={handleSelect(course.item.url)}
                                    onSelect={() => {
                                        setIsOpen(false);
                                        redirect(`/review${course.item.url}`);
                                    }}
                                >
                                    {course.item.title} - {course.item.desc}
                                </CommandItem>
                            ))}
                        </CommandGroup>
                    )}
                    {results && isOpen && results.instructors.length > 0 && (
                        <CommandGroup heading="Instructors">
                            {results?.instructors.map((ins) => (
                                <CommandItem
                                    key={ins.item.url}
                                    // onSelect={handleSelect(ins.item.url)}
                                    onSelect={() => {
                                        setIsOpen(false);
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
