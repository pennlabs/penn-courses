import { cn } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import SearchBar from "./SearchBar";

export default function Header() {
    return (
        <header
            className={cn([
                "bg-white",
                "w-full",
                "shadow-md",
                "p-5",
                "border",
                "border-[#f3f3f3]",
                "flex",
                "flex-row",
            ])}
        >
            <Link href="/">
                <Logo />
            </Link>
            <SearchBar header />
        </header>
    );
}

function Logo() {
    return (
        <Image src={`/image/logo.png`} alt="PCR Logo" width={36} height={36} />
    );
}
