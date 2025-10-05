import Header from "@/components/Header";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <div>
      <Header />
      <div className={cn("flex", "flex-col", "items-center", "pt-36", "pb-12")}>
        <h2 className={cn("text-lg", "font-bold")}>Page Not Found</h2>
        <p className={cn("text-xs")}>
          If this problem persists, please contact us at{" "}
          <a href="mailto:contact@pennlabs.org">support@penncoursereview.com</a>
        </p>
      </div>
    </div>
  );
}
