import { AutocompleteResult } from "@/lib/types";
import {
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

interface SearchDropdownProps {
  results: AutocompleteResult | null;
  isOpen: boolean;
  onSelect: (url: string) => void;
}

export default function SearchDropdown({
  results,
  isOpen,
  onSelect,
}: SearchDropdownProps) {
  const hasResults = results && isOpen;
  const hasDepartments = hasResults && results.departments.length > 0;
  const hasCourses = hasResults && results.courses.length > 0;
  const hasInstructors = hasResults && results.instructors.length > 0;
  const hasNoResults =
    hasResults && !hasDepartments && !hasCourses && !hasInstructors;

  return (
    <CommandList>
      {hasNoResults && <CommandEmpty>No results found</CommandEmpty>}

      {hasDepartments && (
        <CommandGroup heading="Departments">
          {results!.departments.map((dept) => (
            <CommandItem
              key={dept.item.url}
              onSelect={() => onSelect(dept.item.url)}
            >
              {dept.item.title} - {dept.item.desc}
            </CommandItem>
          ))}
        </CommandGroup>
      )}

      {hasCourses && (
        <CommandGroup heading="Courses">
          {results!.courses.map((course) => (
            <CommandItem
              key={course.item.url}
              onSelect={() => onSelect(course.item.url)}
            >
              {course.item.title} - {course.item.desc}
            </CommandItem>
          ))}
        </CommandGroup>
      )}

      {hasInstructors && (
        <CommandGroup heading="Instructors">
          {results!.instructors.map((ins) => (
            <CommandItem
              key={ins.item.url}
              onSelect={() => onSelect(ins.item.url)}
            >
              {ins.item.title} - {ins.item.desc}
            </CommandItem>
          ))}
        </CommandGroup>
      )}
    </CommandList>
  );
}
