import { cn } from "@/lib/utils";
import Image from "next/image";

export default function Home() {
    return (
        <div className={cn("flex", "flex-col", "items-center")}>
            <div className={cn("flex", "justify-center")}>
                <Logo />{" "}
                <h1 className={cn("text-5xl", "ml-3")}>Penn Course Review</h1>
            </div>
            <a href="/review">Review page</a>
        </div>
    );
}

function Logo() {
    return (
        <Image src={`/image/logo.png`} alt="PCR Logo" width={64} height={64} />
    );
}
