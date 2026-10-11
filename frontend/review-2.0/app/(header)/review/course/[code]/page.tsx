import Card from "@/components/Card";
import { apiFetch, apiReviewData } from "@/lib/api";
import { AutocompleteData, type Course } from "@/lib/types";
import { cn } from "@/lib/utils";

interface CourseParams {
    code: string;
    semester: string;
}

export async function generateStaticParams() {
    // Old system: new page for course and for semester
    // New: Static rendered for course and query parameter semester=2025A to change the view
    const response = await apiFetch("/api/review/autocomplete");
    const data: AutocompleteData = await response.json();
    return [...new Set(data.courses.map((course) => course.title))].map(
        (courseTitle) => ({
            code: courseTitle,
        })
    );
}

export default async function Course({
    params,
}: {
    params: Promise<CourseParams>;
}) {
    const { code } = await params;
    const response = await apiReviewData("course", code);
    const data: Course = await response.json();
    console.log(data);
    return (
        <div id="review" className={cn("mx-[20%]")}>
            <Card>
                <h3>{data.code}</h3>
            </Card>
        </div>
    );
}
