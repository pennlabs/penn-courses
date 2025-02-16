import { cn } from "@/lib/utils";
import Image from "next/image";

export default function Header() {
    return (
        <header
            className={cn([
                "bg-white",
                "min-h-[80px]",
                "shadow-md",
                "p-5",
                "border",
                "border-[#f3f3f3]",
            ])}
        >
            <Logo />{" "}
        </header>
    );
}

function Logo() {
    return (
        <Image src={`/image/logo.png`} alt="PCR Logo" width={36} height={36} />
    );
}
