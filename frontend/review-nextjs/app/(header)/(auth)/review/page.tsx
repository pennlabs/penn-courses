"use client";
import { cn } from "@/lib/utils";

export default function Review() {
    // const { data: session } = useSession();

    return (
        <div id="review" className={cn("mx-[20%]")}>
            <p>Static data</p>
            {/* {session ? <ReviewPage /> : <p>Not authenticated</p>} */}
        </div>
    );
}

function ReviewPage() {
    return (
        <p>
            Secret static data
            {/* Secret data that needs authentication {auth.isAuthenticated}{" "} */}
            {/* {auth.user?.profile.email} */}
        </p>
    );
}
