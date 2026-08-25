import React from "react";

/**
 * Small line icons for the tool trace, drawn on a 24×24 grid and inheriting
 * `currentColor` so the node styling decides their color.
 */
const Svg = ({ children }: { children: React.ReactNode }) => (
    <svg
        viewBox="0 0 24 24"
        width="11"
        height="11"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
    >
        {children}
    </svg>
);

const Search = () => (
    <Svg>
        <circle cx="11" cy="11" r="7" />
        <path d="M20 20l-3.6-3.6" />
    </Svg>
);

const Book = () => (
    <Svg>
        <path d="M4 5.5A1.5 1.5 0 015.5 4H19v14H5.5A1.5 1.5 0 004 19.5z" />
        <path d="M4 19.5A1.5 1.5 0 015.5 18H19v2.5H5.5A1.5 1.5 0 014 19.5z" />
    </Svg>
);

const Star = () => (
    <Svg>
        <path d="M12 3.5l2.6 5.3 5.9.9-4.2 4.1 1 5.8-5.3-2.8-5.3 2.8 1-5.8L3.5 9.7l5.9-.9z" />
    </Svg>
);

const Calendar = () => (
    <Svg>
        <rect x="3.5" y="5" width="17" height="15.5" rx="2" />
        <path d="M3.5 10h17M8 3v4M16 3v4" />
    </Svg>
);

const CalendarPlus = () => (
    <Svg>
        <path d="M20.5 11.5V7a2 2 0 00-2-2h-13a2 2 0 00-2 2v11.5a2 2 0 002 2H12" />
        <path d="M3.5 10h17M8 3v4M16 3v4" />
        <path d="M17.5 14.5v6M14.5 17.5h6" />
    </Svg>
);

const CalendarMinus = () => (
    <Svg>
        <path d="M20.5 11.5V7a2 2 0 00-2-2h-13a2 2 0 00-2 2v11.5a2 2 0 002 2H12" />
        <path d="M3.5 10h17M8 3v4M16 3v4" />
        <path d="M14.5 17.5h6" />
    </Svg>
);

/** A checklist, for degree requirements. */
const Checklist = () => (
    <Svg>
        <path d="M8 4h9a2 2 0 012 2v13a2 2 0 01-2 2H7a2 2 0 01-2-2V6a2 2 0 012-2h1z" />
        <path d="M9 3.5h6v2.5H9zM9 11l1.6 1.6L14 9.2M9 16.5h5" />
    </Svg>
);

const Dot = () => (
    <Svg>
        <circle cx="12" cy="12" r="3.5" fill="currentColor" stroke="none" />
    </Svg>
);

export const TOOL_ICONS: { [name: string]: () => JSX.Element } = {
    search_courses: Search,
    get_course: Book,
    get_course_reviews: Star,
    get_my_schedules: Calendar,
    add_to_schedule: CalendarPlus,
    remove_from_schedule: CalendarMinus,
    get_my_degree_plan: Checklist,
};

export const FallbackIcon = Dot;
