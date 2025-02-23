import type { Metadata } from "next";
import "./globals.css";
import { cn } from "@/lib/utils";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
    title: "Penn Course Review",
    description: "Made by Penn Labs",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={cn("antialiased", "flex", "flex-col")}>
                {children}
                <Footer />
            </body>
        </html>
    );
}
