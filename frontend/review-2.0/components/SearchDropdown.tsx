import {
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { AutocompleteData } from "@/lib/types";

interface SearchDropdownProps {
  results: AutocompleteData | null;
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
          {results.departments.map((dept) => (
            <CommandItem
              key={dept.url}
              onSelect={() => onSelect(dept.url)}
            >
              {dept.title} - {dept.desc}
            </CommandItem>
          ))}
        </CommandGroup>
      )}

      {hasCourses && (
        <CommandGroup heading="Courses">
          {results.courses.map((course) => (
            <CommandItem
              key={course.url}
              onSelect={() => onSelect(course.url)}
            >
              {course.title} - {course.desc}
            </CommandItem>
          ))}
        </CommandGroup>
      )}

      {hasInstructors && (
        <CommandGroup heading="Instructors">
          {results.instructors.map((ins) => (
            <CommandItem
              key={ins.url}
              onSelect={() => onSelect(ins.url)}
            >
              {ins.title} - {ins.desc}
            </CommandItem>
          ))}
        </CommandGroup>
      )}
    </CommandList>
  );
}
