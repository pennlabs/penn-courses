import { cn } from "@/lib/utils";
import { useEffect } from "react";

export default function Review() {
    return (
        <div id="review" className={cn("mx-[20%]")}>
            <p>YOURE AUTHENTICATED! Static protected data</p>
        </div>
    );
}
