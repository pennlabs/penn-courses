import { useEffect, useState, useCallback } from "react";
import fuzzysort from "fuzzysort";
import { AutocompleteObject, AutocompleteData } from "@/lib/types";
import { apiFetch } from "@/lib/api";

type PreparedData = {
  departments: (AutocompleteObject & { search_desc: Fuzzysort.Prepared })[];
  instructors: (AutocompleteObject & { search_desc: Fuzzysort.Prepared })[];
  courses: (AutocompleteObject & { search_title: Fuzzysort.Prepared; search_desc: Fuzzysort.Prepared })[];
};

// Expand course string formats (CIS 160 → CIS-160, CIS160, etc.)
function expandCombo(course: string) {
  const [dept, num] = course.split(" ");
  return `${course} ${dept}-${num} ${dept}${num}`;
}

const normalizeDesc = (desc: string | string[]) => Array.isArray(desc) ? desc.join(" ") : desc;

export function useAutocomplete() {
  const [prepared, setPrepared] = useState<PreparedData | null>(null);

  // Load autocomplete data once
  useEffect(() => {
    async function loadData() {
      try {
        const response = await apiFetch("/api/review/autocomplete");
        const data: AutocompleteData = await response.json();

        // Set Prepared data
        setPrepared({
          departments: data.departments.map(i => ({
            ...i,
            search_desc: fuzzysort.prepare(normalizeDesc(i.desc)),
          })),

          courses: data.courses.map(c => ({
              ...c,
              search_title: fuzzysort.prepare(expandCombo(c.title)),
              search_desc: fuzzysort.prepare(normalizeDesc(c.desc)),
          })),

          instructors: data.instructors.map(i => ({
            ...i,
            search_desc: fuzzysort.prepare(normalizeDesc(i.desc)),
          })),
        });
      } catch (e) {
        console.error(e);
        setPrepared(null);
      }
    }

    loadData();
  }, []);

  // Search function
  const autocomplete = useCallback(
    (inputValue: string) => {
      if (!inputValue.trim() || prepared == null) {
        return null;
      }

      return {
        departments: fuzzysort
          .go<AutocompleteObject>(inputValue, prepared.departments, {
            keys: ["title", "search_desc"],
            threshold: -200,
            limit: 10
          }).map((r) => r.obj),
        courses: fuzzysort.go<AutocompleteObject>(inputValue, prepared.courses, {
            keys: ["search_title", "search_desc"],
            threshold: -200,
            limit: 25
          }).map((r) => r.obj),
        instructors: fuzzysort
          .go<AutocompleteObject>(inputValue, prepared.instructors, {
            keys: ["title", "search_desc"],
            threshold: -200,
            limit: 10
          }).map((r) => r.obj),
      };
    },
    [prepared]
  );

  return autocomplete;
}
