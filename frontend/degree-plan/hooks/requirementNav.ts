import { Rule } from "@/types";

type RuleListener = (ruleId: number) => void;

const ruleListeners = new Set<RuleListener>();
const ruleCycle = new Map<string, number>();

export function semesterDomId(semester: string) {
  return `semester-${semester}`;
}

export function ruleDomId(ruleId: number) {
  return `rule-${ruleId}`;
}

export function ghostDomId(placement: { slot_ids?: string[]; full_code?: string | null; kind?: string }) {
  return `ghost-${placement.slot_ids?.[0] || placement.full_code || placement.kind || "item"}`;
}

export function subscribeRuleNav(listener: RuleListener) {
  ruleListeners.add(listener);
  return () => {
    ruleListeners.delete(listener);
  };
}

/** Jump to one rule this course fills. Another click on the same course moves to the next rule. */
export function navigateToRule(cycleKey: string, ruleIds: number[]) {
  const ids = ruleIds.filter((id) => id != null);
  if (!ids.length) return;
  const index = ruleCycle.get(cycleKey) ?? 0;
  const ruleId = ids[index % ids.length];
  ruleCycle.set(cycleKey, (index + 1) % ids.length);
  ruleListeners.forEach((listener) => listener(ruleId));
}

export function containsRule(rules: Rule[] | undefined, ruleId: number): boolean {
  if (!rules) return false;
  return rules.some((rule) => rule.id === ruleId || containsRule(rule.rules, ruleId));
}

function scrollingAncestor(element: HTMLElement) {
  let node = element.parentElement;
  while (node) {
    const overflow = getComputedStyle(node).overflowY;
    if (
      (overflow === "auto" || overflow === "scroll") &&
      node.scrollHeight > node.clientHeight + 4
    ) {
      return node;
    }
    node = node.parentElement;
  }
  return null;
}

/** Put the requirement in the middle of the requirements panel, not the window. */
export function centerInRequirements(ruleId: number) {
  const element = document.getElementById(ruleDomId(ruleId));
  if (!element) return;
  const panel = document.getElementById("requirements-scroll");
  const scroller =
    panel && panel.contains(element) && panel.scrollHeight > panel.clientHeight + 4
      ? panel
      : scrollingAncestor(element);
  if (!scroller) {
    element.scrollIntoView({ behavior: "smooth", block: "center" });
  } else {
    const elementRect = element.getBoundingClientRect();
    const scrollerRect = scroller.getBoundingClientRect();
    const top =
      scroller.scrollTop +
      (elementRect.top - scrollerRect.top) -
      (scroller.clientHeight - elementRect.height) / 2;
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }
  flashElement(ruleDomId(ruleId));
}

export function flashElement(id: string) {
  const element = document.getElementById(id);
  if (!element) return;
  element.classList.remove("nav-flash");
  void element.offsetWidth;
  element.classList.add("nav-flash");
  window.setTimeout(() => element.classList.remove("nav-flash"), 2200);
}

/** Scroll the schedule to the semester that holds this ghost, then flash the card. */
export function scrollToPlacement(placement: { semester?: string | null; slot_ids?: string[]; full_code?: string | null; kind?: string }) {
  if (!placement.semester) return;
  document.getElementById(semesterDomId(placement.semester))?.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
  window.setTimeout(() => flashElement(ghostDomId(placement)), 280);
}
