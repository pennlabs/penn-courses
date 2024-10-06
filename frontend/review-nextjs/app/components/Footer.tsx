//import { getLogoutUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Heart } from "lucide-react";
import Link from "next/link";

export default function Footer() {
    return (
        <footer className={cn("block", "w-full", "text-xs")}>
            <Link href="/about">About</Link> | <Link href="/faq">FAQs</Link> |{" "}
            <a
                target="_blank"
                rel="noopener noreferrer"
                href="https://airtable.com/appFRa4NQvNMEbWsA/shrCCsGC2BjUif5Wx"
            >
                Feedback
            </a>{" "}
            | <a href={"TODO"}>Logout</a>
            <p id="copyright" className={cn("mx-4")}>
                Made with{" "}
                <Heart color="#F56F71" size={14} className={cn("inline")} /> by{" "}
                <a href="https://pennlabs.org">
                    <strong>Penn Labs</strong>
                </a>{" "}
            </p>
        </footer>
    );
}
