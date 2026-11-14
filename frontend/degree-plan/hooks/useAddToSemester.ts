import { useContext } from "react";
import useSWR from "swr";
import { DegreePlan, DockedCourse, Fulfillment } from "@/types";
import { useSWRCrud } from "@/hooks/swrcrud";
import ToastContext from "@/components/Toast/Toast";

interface SatisfiedRules {
  selected_rules: { id: number }[];
  unselected_rules: { id: number }[];
  new_selected_rules: { id: number; title: string }[];
  legal: boolean;
}

/**
 * Adds a course to a semester of the plan, the same way whether it was dropped or added from a
 * button. A course already in the plan only moves; anything else is allocated to rules first,
 * and leaves the dock if it was there.
 * `ruleId` is the rule the course came from, or -1 when it came from no rule.
 * Resolves to whether the course was added; a failure is reported with a toast.
 */
const useAddToSemester = (planId: DegreePlan["id"] | null | undefined) => {
  const showToast = useContext(ToastContext);
  // The fulfillments api uses POST for updates too: it creates the row if it doesn't exist.
  const { createOrUpdate } = useSWRCrud<Fulfillment>(
    `/api/degree/degreeplans/${planId}/fulfillments`,
    {
      idKey: "full_code",
      createDefaultOptimisticData: { semester: null, rules: [] },
    }
  );

  const { data: docked = [] } = useSWR<DockedCourse[]>("/api/degree/docked");
  const { remove: removeFromDock } = useSWRCrud<DockedCourse>(
    "/api/degree/docked",
    {
      idKey: "full_code",
    }
  );

  return async (
    fullCode: string,
    semester: string,
    { ruleId = -1, inPlan = false }: { ruleId?: number; inPlan?: boolean } = {}
  ): Promise<boolean> => {
    if (!planId) return false;
    const failed = () => {
      showToast(`Couldn't add ${fullCode.replace("-", " ")}. Try again.`, true);
      return false;
    };
    if (inPlan) {
      try {
        await createOrUpdate({ semester }, fullCode);
        return true;
      } catch {
        return failed();
      }
    }

    let data: SatisfiedRules;
    try {
      const response = await fetch(
        `/api/degree/satisfied-rule-list/${planId}/${fullCode}/${ruleId}?semester=${encodeURIComponent(semester)}`
      );
      if (!response.ok) throw new Error(`satisfied-rule-list: ${response.status}`);
      data = await response.json();
      await createOrUpdate(
        {
          rules: data.selected_rules.map((rule) => rule.id),
          unselected_rules: data.unselected_rules.map((rule) => rule.id),
          legal: data.legal,
          semester,
        },
        fullCode
      );
    } catch {
      return failed();
    }
    // Only once it's in the plan, so a failure above leaves it in the dock.
    if (docked.some((course) => course.full_code === fullCode))
      removeFromDock(fullCode);

    // TODO: This doesn't work for explicitly listed courses.
    data.new_selected_rules.forEach((rule) => {
      if (ruleId === -1) {
        showToast(`${fullCode} fulfilled ${rule.title}!`, false);
      } else if (rule.id !== ruleId) {
        showToast(`${fullCode} also fulfilled ${rule.title}!`, false);
      }
    });
    return true;
  };
};

export default useAddToSemester;
