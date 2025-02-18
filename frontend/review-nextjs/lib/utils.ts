import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { SearchResult } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * @returns {string | boolean} The CSRF token used by backend
 */
const getCsrf = (): string | boolean => {
  return document.cookie &&
    document.cookie
        .split("; ")
        .reduce(
            (acc: string | boolean, cookie) =>
                acc ||
                (cookie.substring(0, "csrftoken".length + 1) ===
                    "csrftoken=" &&
                    decodeURIComponent(
                        cookie.substring("csrftoken=".length)
                    )),
            false
        );
};


const dummyResults: SearchResult = {
  Courses: [
      {
          code: "CIS 120",
          title: "Programming Languages and Techniques",
          description:
              "Introduction to programming languages, including functional, object-oriented, and logic programming. Programming assignments in several languages.",
          semester: "Fall 2023",
          quality: 3.5,
          work: 2.5,
          difficulty: 2.0,
          current: true,
          instructors: ["Prof. Smith", "Prof. Johnson"],
          cleanCode: "Yes",
      },
      {
          code: "CIS 121",
          title: "Data Structures and Algorithms",
          description:
              "Introduction to data structures and algorithms. Topics include arrays, linked lists, trees, graphs, and sorting algorithms.",
          semester: "Spring 2024",
          quality: 4.0,
          work: 3.0,
          difficulty: 3.5,
          current: false,
          instructors: ["Prof. Brown"],
          cleanCode: "No",
      },
  ],
  Departments: [
      { code: "CIS", name: "Computer and Information Science" },
      { code: "MATH", name: "Mathematics" },
  ],
  Instructors: [
      {
          name: "Prof. Smith",
          desc: "Expert in programming languages",
          id: "1",
      },
      {
          name: "Prof. Johnson",
          desc: "Expert in software engineering",
          id: "2",
      },
  ],
};

export const fetchDummyResults = async (query: string): Promise<SearchResult> => {
    return new Promise((resolve) => {
        resolve(dummyResults);
        // setTimeout(() => {
        //     console.log("Making network request");
        //     resolve(dummyResults);
        // }, 100);
    });
};

export default getCsrf;
