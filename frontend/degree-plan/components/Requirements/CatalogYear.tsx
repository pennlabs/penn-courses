import styled from "@emotion/styled";
import { useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";
import { getFetcher, postFetcher } from "@/hooks/swrcrud";
import { Item, Menu } from "../FourYearPlan/SelectListDropdown";
import { DegreePlan } from "@/types";
import {
  OPEN_ENDED_YEAR,
  PlanProgram,
  ProgramKind,
  startingYearsLabels,
} from "@/utils/programs";

const Row = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.75rem 0.35rem;
  font-size: 0.78rem;
  color: var(--primary-color-extra-dark);

  > i {
    font-size: 0.75rem;
    opacity: 0.8;
  }
`;

const pillStyle = (kind: ProgramKind) => `
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.18rem 0.6rem;
  border: none;
  border-radius: 999px;
  background: var(--program-${kind}-bg);
  color: var(--program-${kind});
  font: inherit;
  font-weight: 600;
`;

const Pill = styled.span<{ $kind: ProgramKind }>`
  ${(props) => pillStyle(props.$kind)}
`;

const PillButton = styled.button<{ $kind: ProgramKind }>`
  ${(props) => pillStyle(props.$kind)}
  cursor: pointer;

  i {
    font-size: 0.6rem;
    transition: transform 200ms ease;
  }

  &[aria-expanded="true"] i {
    transform: rotate(180deg);
  }

  &:hover:not(:disabled) {
    filter: brightness(0.95);
  }

  &:disabled {
    cursor: progress;
  }

  &:focus-visible {
    outline: 2px solid var(--modal-button-color);
    outline-offset: 1px;
  }

  @media (prefers-reduced-motion: reduce) {
    i {
      transition: none;
    }
  }
`;

const Anchor = styled.span`
  position: relative;
`;

const YearMenu = styled(Menu)`
  left: 0;
  z-index: 1001; /* above the tab bar */
  min-width: 13rem;
`;

const YearItem = styled(Item)`
  justify-content: space-between;
  font-size: 0.875rem;

  &:focus-visible {
    outline: 2px solid var(--primary-color-xx-dark);
    outline-offset: -2px;
  }
`;

const Error = styled.span`
  color: var(--error-color);
`;

const ReloadButton = styled.button`
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  color: inherit;
  text-decoration: underline;
  cursor: pointer;
`;

interface CatalogYearProps {
  program: PlanProgram;
  planId: DegreePlan["id"];
  // Runs the save in turn with the plan's other pending changes (e.g. waivers).
  queueSave: (save: () => Promise<unknown>) => Promise<unknown>;
  // Who the version being loaded is for, then null once it's shown or has failed.
  onSwitching: (label: string | null) => void;
  // Runs once the next version has loaded, before it replaces this one.
  beforeSwap: () => Promise<void>;
}

/**
 * Which catalog year a program's requirements come from: picked from the student's starting
 * year, and changeable here, e.g. for a student who declared under a later catalog.
 */
const CatalogYear = ({
  program,
  planId,
  queueSave,
  onSwitching,
  beforeSwap,
}: CatalogYearProps) => {
  const { mutate } = useSWRConfig();
  const [saving, setSaving] = useState(false);
  // Once saved, the plan no longer holds the old version, so only a reload is safe.
  const [failed, setFailed] = useState<"switch" | "reload" | null>(null);
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLSpanElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);
  const id = `catalog-year-${program.relation}-${program.id}`;
  const labels = startingYearsLabels(
    program.catalogYears.map(({ year }) => year)
  );
  const versions = program.catalogYears.map((version, i) => ({
    ...version,
    label: labels[i],
  }));
  const current = versions.findIndex((version) => version.id === program.id);

  useEffect(() => {
    if (!open) return undefined;
    itemRefs.current[current]?.focus();
    const close = (event: MouseEvent) => {
      if (!anchorRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open, current]);

  // Requirements that apply to every year have no starting year to point out or switch from.
  if (versions.length < 2 && program.year === OPEN_ENDED_YEAR) return null;
  if (versions.length < 2)
    return (
      <Row>
        <i className="far fa-calendar" aria-hidden />
        For students starting
        <Pill $kind={program.kind}>{versions[current].label}</Pill>
      </Row>
    );

  const planKey = `/api/degree/degreeplans/${planId}`;
  const closeMenu = () => {
    setOpen(false);
    buttonRef.current?.focus();
  };
  const fulfillmentsKey = `${planKey}/fulfillments`;
  // Courses and requirements are shown together, so progress never counts one against the
  // other's old version.
  const show = async (plan: unknown) => {
    const fulfillments = await getFetcher(fulfillmentsKey);
    await beforeSwap();
    await Promise.all([
      mutate(fulfillmentsKey, fulfillments, { revalidate: false }),
      mutate(planKey, plan, { revalidate: false }),
    ]);
  };
  const run = (task: () => Promise<void>) => {
    setSaving(true);
    setFailed(null);
    queueSave(task).finally(() => {
      setSaving(false);
      onSwitching(null);
    });
  };
  const reload = async () => {
    try {
      await show(await getFetcher(planKey));
    } catch {
      setFailed("reload");
    }
  };
  const switchTo = (version: typeof versions[number]) => {
    closeMenu();
    if (version.id === program.id) return;
    onSwitching(version.label);
    run(async () => {
      let plan;
      try {
        plan = await postFetcher(`${planKey}/catalog-year`, {
          relation: program.relation,
          from_id: program.id,
          to_id: version.id,
        });
      } catch {
        setFailed("switch");
        return;
      }
      try {
        await show(plan);
      } catch {
        await reload();
      }
    });
  };

  return (
    <Row>
      <i className="far fa-calendar" aria-hidden />
      <span id={`${id}-label`}>For students starting</span>
      <Anchor ref={anchorRef}>
        <PillButton
          ref={buttonRef}
          type="button"
          $kind={program.kind}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-labelledby={`${id}-label ${id}-button`}
          id={`${id}-button`}
          disabled={saving}
          onClick={() => setOpen(!open)}
        >
          {versions[current].label}
          <i
            className={
              saving ? "fas fa-spinner fa-spin" : "fas fa-chevron-down"
            }
            aria-hidden
          />
        </PillButton>
        <YearMenu
          role="menu"
          $open={open}
          onKeyDown={(e) => {
            const items = itemRefs.current.filter(Boolean) as HTMLDivElement[];
            const at = items.indexOf(document.activeElement as HTMLDivElement);
            if (e.key === "Escape") closeMenu();
            else if (e.key === "ArrowDown")
              items[Math.min(at + 1, items.length - 1)]?.focus();
            else if (e.key === "ArrowUp") items[Math.max(at - 1, 0)]?.focus();
            else if (e.key === "Tab") setOpen(false);
            else return;
            if (e.key !== "Tab") e.preventDefault();
          }}
        >
          {versions.map((version, i) => (
            <YearItem
              key={version.id}
              ref={(element) => {
                itemRefs.current[i] = element;
              }}
              role="menuitemradio"
              aria-checked={i === current}
              tabIndex={open ? 0 : -1}
              $isActive={i === current}
              onClick={() => switchTo(version)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  switchTo(version);
                }
              }}
            >
              {version.label}
              {i === current && <i className="fas fa-check" aria-hidden />}
            </YearItem>
          ))}
        </YearMenu>
      </Anchor>
      {failed === "switch" && (
        <Error role="alert">Couldn&apos;t change it. Try again.</Error>
      )}
      {failed === "reload" && (
        <Error role="alert">
          Changed, but couldn&apos;t load it.{" "}
          <ReloadButton type="button" onClick={() => run(reload)}>
            Reload
          </ReloadButton>
        </Error>
      )}
    </Row>
  );
};

export default CatalogYear;
