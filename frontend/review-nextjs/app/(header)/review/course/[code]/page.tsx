import { apiFetch, apiReviewData } from "@/lib/api";
import { AutocompleteData } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useEffect } from "react";

interface CourseParams {
    code: string;
    semester: string;
}

export async function generateStaticParams() {
    // Old system: new page for course and for semester
    // New: Static rendered for course and query parameter semester=2025A to change the view
    const response = await apiFetch("/api/review/autocomplete");
    const data: AutocompleteData = await response.json();
    return data.courses.map((course) => ({
        code: course.title,
    }));
}

export default async function Course({
    params,
}: {
    params: Promise<CourseParams>;
}) {
    const { code } = await params;
    // const response = await apiReviewData("course", code);
    // const data = await response.json();
    // console.log(data);
    return (
        <div id="review" className={cn("mx-[20%]")}>
            <p>YOURE AUTHENTICATED! Static protected data</p>
        </div>
    );
}
