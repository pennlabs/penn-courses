"use client";
import Header from "@/components/Header";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  const router = useRouter();
  return (
    <div className={cn("flex", "flex-col", "items-center")}>
      <h2>Something went wrong!</h2>
      <h3>{error.message}</h3>
      <button
        onClick={() => {
          router.push("/");
        }}
      >
        Go back
      </button>
    </div>
  );
}
