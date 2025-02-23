import SearchBar from "@/components/SearchBar";
import { cn } from "@/lib/utils";
import Image from "next/image";

export default function Home() {
    return (
        <div className={cn("flex", "flex-col", "items-center", "py-36")}>
            <div className={cn("flex", "justify-center", "my-8")}>
                <Logo />{" "}
                <h1 className={cn("text-5xl", "ml-3")}>Penn Course Review</h1>
            </div>
            <SearchBar />
        </div>
    );
}

function Logo() {
    return (
        <Image src={`/image/logo.png`} alt="PCR Logo" width={64} height={64} />
    );
}
