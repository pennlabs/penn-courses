import { cn } from "@/lib/utils";

export default function Card({ children }: { children?: React.ReactNode }) {
  return (
    <div className={cn("bg-white", "rounded-lg", "shadow-sm", "p-7")}>
      {children}
    </div>
  );
}
