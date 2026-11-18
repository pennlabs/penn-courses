import { useContext } from "react";
import useSWR, { useSWRConfig } from "swr";
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
  const { mutate } = useSWRConfig();
  const fulfillmentsKey = `/api/degree/degreeplans/${planId}/fulfillments`;
  // The fulfillments api uses POST for updates too: it creates the row if it doesn't exist.
  const { createOrUpdate } = useSWRCrud<Fulfillment>(fulfillmentsKey, {
    idKey: "full_code",
    createDefaultOptimisticData: { semester: null, rules: [] },
  });

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

    const placeholder = ({
      full_code: fullCode,
      semester,
      course: null,
      rules: [],
      unselected_rules: [],
      overrides: [],
      legal: true,
      level: null,
    } as unknown) as Fulfillment;
    // A course dragged from search or a requirement can already be in the plan.
    let replaced: Fulfillment | undefined;
    await mutate(
      fulfillmentsKey,
      (list: Fulfillment[] = []) => {
        replaced = list.find((f) => f.full_code === fullCode);
        return [...list.filter((f) => f.full_code !== fullCode), placeholder];
      },
      { revalidate: false }
    );
    // Hidden from the dock straight away too, but only deleted from it once the course is saved.
    const wasDocked = docked.some((course) => course.full_code === fullCode);
    if (wasDocked)
      mutate(
        "/api/degree/docked",
        (list: DockedCourse[] = []) =>
          list.filter((course) => course.full_code !== fullCode),
        { revalidate: false }
      );

    let data: SatisfiedRules;
    try {
      const response = await fetch(
        `/api/degree/satisfied-rule-list/${planId}/${fullCode}/${ruleId}?semester=${encodeURIComponent(
          semester
        )}`
      );
      if (!response.ok)
        throw new Error(`satisfied-rule-list: ${response.status}`);
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
      // Only undo our placeholder, not a later change to the same course.
      mutate(
        fulfillmentsKey,
        (list: Fulfillment[] = []) => {
          if (!list.includes(placeholder)) return list;
          const rest = list.filter((f) => f !== placeholder);
          return replaced ? [...rest, replaced] : rest;
        },
        { revalidate: false }
      );
      if (wasDocked) mutate("/api/degree/docked");
      return failed();
    }
    if (wasDocked) removeFromDock(fullCode);

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
