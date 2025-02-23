import { cn } from "@/lib/utils";
import { Rating } from "@/lib/types";

export default function ScoreBox({
    children,
    rating,
}: Readonly<{
    children: React.ReactNode;
    rating: Rating;
}>) {
    return (
        <div
            className={cn(
                "inline-block",
                "mx-1",
                "h-[70px]",
                "w-[70px]",
                "rounded",
                "text-center",
                rating == Rating.Bad
                    ? "bg-[#ffc107]"
                    : rating == Rating.Okay
                    ? "bg-[#6274f1]"
                    : rating == Rating.Good
                    ? "bg-[#76bf96]"
                    : "bg-white"
            )}
        >
            <div className={cn("my-4", "text-2xl", "text-white")}>
                {children}
            </div>
        </div>
    );
}
