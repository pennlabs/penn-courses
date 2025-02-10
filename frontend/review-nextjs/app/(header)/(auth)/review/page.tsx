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
