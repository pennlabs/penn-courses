"use client";

import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  Command,
  CommandInput,
} from "@/components/ui/command";
import { useAutocomplete } from "@/hooks/useAutocomplete";
import SearchDropdown from "./SearchDropdown";

export default function SearchBar({ header }: { header?: boolean }) {
  const [query, setQuery] = useState("");
  const autocomplete = useAutocomplete();
  const [isOpen, setIsOpen] = useState(false);
  const commandRef = useRef<HTMLDivElement>(null);

  const router = useRouter();

  const handleSelect = (url: string) => {
    setIsOpen(false);
    router.push(url);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        commandRef.current &&
        !commandRef.current.contains(event.target as Node)
      ) {
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
        <SearchDropdown 
          results={autocomplete(query)}
          isOpen={isOpen}
          onSelect={handleSelect}
        />
      </Command>
    </div>
  );
}
