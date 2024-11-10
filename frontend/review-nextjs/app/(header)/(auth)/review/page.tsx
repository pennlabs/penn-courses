"use client";
import Skeleton from "@/components/Skeleton";
import { cn } from "@/lib/utils";
import { useEffect } from "react";
import { useAuth } from "react-oidc-context";

/*
On error with fetching data
try {
    userManager.signinSilent()
} catch (error) {
    userManager.signinRedirect()
}
*/

export default function Review() {
    const auth = useAuth();

    return (
        <div id="review" className={cn("mx-[20%]")}>
            {auth.isLoading ? <Skeleton /> : <ReviewPage />}
        </div>
    );
}

function ReviewPage() {
    const auth = useAuth();

    return (
        <p>
            Secret data that needs authentication {auth.isAuthenticated}{" "}
            {auth.user?.profile.email}
        </p>
    );
}
