"use client";
import { cn } from "@/lib/utils";

export default function Review() {
    return (
        <div id="review" className={cn("mx-[20%]")}>
            {/* {auth.isLoading ? <Skeleton /> : <ReviewPage />} */}
        </div>
    );
}

function ReviewPage() {
    return (
        <p>
            Secret data
            {/* Secret data that needs authentication {auth.isAuthenticated}{" "} */}
            {/* {auth.user?.profile.email} */}
        </p>
    );
}
