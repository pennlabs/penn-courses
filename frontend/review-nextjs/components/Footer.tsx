"use client";
import { cn } from "@/lib/utils";
import { Heart } from "lucide-react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className={cn("block", "text-xs", "mx-auto", "text-center")}>
      <Link href="/about">About</Link> | <Link href="/faq">FAQs</Link> |{" "}
      <a
        target="_blank"
        rel="noopener noreferrer"
        href="https://airtable.com/appFRa4NQvNMEbWsA/shrCCsGC2BjUif5Wx"
      >
        Feedback
      </a>
      <p id="copyright">
        Made with{" "}
        <Heart
          color="#F56F71"
          size={14}
          className={cn("inline")}
          fill="#F56F71"
        />{" "}
        by{" "}
        <a href="https://pennlabs.org">
          <strong>Penn Labs</strong>
        </a>{" "}
      </p>
    </footer>
  );
}
