import { useEffect, useState, useCallback } from "react";
import fuzzysort from "fuzzysort";
import { AutocompleteObject } from "@/lib/types";
import { apiAutocomplete } from "@/lib/api";
import { expandCourseCode, normalizeDesc } from "@/lib/utils";

type PreparedData = {
  departments: (AutocompleteObject & { search_desc: Fuzzysort.Prepared })[];
  instructors: (AutocompleteObject & { search_desc: Fuzzysort.Prepared })[];
  courses: (AutocompleteObject & { search_title: Fuzzysort.Prepared; search_desc: Fuzzysort.Prepared })[];
};

export function useAutocomplete() {
  const [preparedData, setPreparedData] = useState<PreparedData | null>(null);

  // Load autocomplete data once
  useEffect(() => {
    async function loadData() {
      try {
        const data = await apiAutocomplete();
        if (!data) {
          throw new Error("Failed to fetch autocomplete data");
        }

        // Set Prepared data
        setPreparedData({
          departments: data.departments.map(i => ({
            ...i,
            search_desc: fuzzysort.prepare(normalizeDesc(i.desc)),
          })),

          courses: data.courses.map(c => ({
              ...c,
              search_title: fuzzysort.prepare(expandCourseCode(c.title)),
              search_desc: fuzzysort.prepare(normalizeDesc(c.desc)),
          })),

          instructors: data.instructors.map(i => ({
            ...i,
            search_desc: fuzzysort.prepare(normalizeDesc(i.desc)),
          })),
        });
      } catch (e) {
        console.error(e);
        setPreparedData(null);
      }
    }

    loadData();
  }, []);

  // Search function
  const autocomplete = useCallback(
    (inputValue: string) => {
      if (!inputValue.trim() || preparedData == null) {
        return null;
      }

      return {
        departments: fuzzysort
          .go<AutocompleteObject>(inputValue, preparedData.departments, {
            keys: ["title", "search_desc"],
            threshold: -200,
            limit: 10
          }).map((r) => r.obj),
        courses: fuzzysort.go<AutocompleteObject>(inputValue, preparedData.courses, {
            keys: ["search_title", "search_desc"],
            threshold: -200,
            limit: 25
          }).map((r) => r.obj),
        instructors: fuzzysort
          .go<AutocompleteObject>(inputValue, preparedData.instructors, {
            keys: ["title", "search_desc"],
            threshold: -200,
            limit: 10
          }).map((r) => r.obj),
      };
    },
    [preparedData]
  );

  return autocomplete;
}
