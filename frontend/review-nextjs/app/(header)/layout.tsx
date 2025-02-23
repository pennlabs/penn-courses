import Header from "@/components/Header";
import { cn } from "@/lib/utils";

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <>
            <Header />
            <main
                className={cn("flex", "flex-col", "items-center", "mx-[10%]")}
            >
                {children}
            </main>
        </>
    );
}
