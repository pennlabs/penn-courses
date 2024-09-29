import { cn } from "@/lib/utils";
import Image from "next/image";

export default function Home() {
    return (
        <div>
            <Title />
            <h1 className={cn("text-5xl")}>Penn Course Review</h1>
        </div>
    );
}

function Title() {
    return (
        <Image src={`/img/logo.png`} alt="PCR Logo" width={64} height={64} />
    );
}
