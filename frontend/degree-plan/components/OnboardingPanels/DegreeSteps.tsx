import { useEffect, useMemo, useRef, useState } from "react";
import Select from "react-select";
import {
  CatalogRow,
  concentrationChoices,
  concentrationKey,
  concentrationLabel,
  defaultYear,
  majorChoices,
  rowKey,
  yearChoices,
} from "@/utils/degreeChoice";
import { Field, FieldLabel, Required, selectStyles } from "./onboardingStyles";

type Option = { value: string; label: string };

const menu = { menuPortalTarget: typeof document !== "undefined" ? document.body : null };

// Major, then concentration when the major has more than one, then catalog year when more
// than one year exists. The year defaults to the plan's start year.
export default function DegreeSteps({
  id,
  rows,
  value,
  startYear,
  isLoading,
  required = false,
  onChange,
}: {
  id: string;
  rows: CatalogRow[];
  value: CatalogRow | null;
  startYear: number | null;
  isLoading: boolean;
  required?: boolean;
  onChange: (row: CatalogRow | null) => void;
}) {
  // undefined follows the saved row. A string or null is a choice the parent has not stored yet.
  const [pendingMajor, setPendingMajor] = useState<string | null | undefined>(undefined);
  const [pendingConcentration, setPendingConcentration] = useState<string | undefined>(undefined);
  const major = pendingMajor !== undefined ? pendingMajor : value ? rowKey(value) : null;

  const majors = useMemo(() => majorChoices(rows), [rows]);
  const concentrations = useMemo(
    () => (major ? concentrationChoices(rows, major) : []),
    [rows, major]
  );
  const concentration =
    pendingConcentration !== undefined
      ? pendingConcentration
      : concentrations.length === 1
      ? concentrationKey(concentrations[0])
      : value && rowKey(value) === major
      ? concentrationKey(value)
      : null;
  const years = useMemo(
    () => (major && concentration != null ? yearChoices(rows, major, concentration) : []),
    [rows, major, concentration]
  );

  const resolved = useMemo(() => {
    if (!years.length) return null;
    const chosen = value && years.some((row) => row.id === value.id) ? value.year : null;
    const year = chosen ?? defaultYear(years.map((row) => row.year), startYear);
    return years.find((row) => row.year === year) ?? null;
  }, [years, value, startYear]);

  const emitted = useRef<number | null | undefined>(undefined);
  useEffect(() => {
    const next = resolved?.id ?? null;
    const current = value?.id ?? null;
    if (next === current) {
      emitted.current = next;
      return;
    }
    if (next === emitted.current) return;
    emitted.current = next;
    onChange(resolved);
    // onChange is the card's setter; depending on it would emit again every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolved, value]);

  const majorOptions: Option[] = majors.map((row) => ({
    value: rowKey(row),
    label: row.major_name || row.major,
  }));
  const concentrationOptions: Option[] = concentrations.map((row) => ({
    value: concentrationKey(row),
    label: concentrationLabel(row),
  }));
  const yearOptions: Option[] = years.map((row) => ({
    value: String(row.year),
    label: String(row.year),
  }));

  return (
    <>
      <Field>
        <FieldLabel htmlFor={`${id}-major`}>
          Major
          {required && <Required />}
        </FieldLabel>
        <Select
          inputId={`${id}-major`}
          options={majorOptions}
          value={majorOptions.find((option) => option.value === major) ?? null}
          onChange={(selected) => {
            setPendingMajor(selected?.value ?? null);
            setPendingConcentration(undefined);
            if (!selected) onChange(null);
          }}
          isClearable
          placeholder="Choose a major"
          styles={selectStyles}
          isLoading={isLoading}
          {...menu}
        />
      </Field>
      {concentrations.length > 1 && (
        <Field>
          <FieldLabel htmlFor={`${id}-concentration`}>Concentration</FieldLabel>
          <Select
            inputId={`${id}-concentration`}
            options={concentrationOptions}
            value={
              concentrationOptions.find((option) => option.value === concentration) ?? null
            }
            onChange={(selected) =>
              setPendingConcentration(selected ? selected.value : undefined)
            }
            isClearable
            placeholder="Choose a concentration"
            styles={selectStyles}
            {...menu}
          />
        </Field>
      )}
      {years.length > 1 && resolved && (
        <Field>
          <FieldLabel htmlFor={`${id}-year`}>Catalog year</FieldLabel>
          <Select
            inputId={`${id}-year`}
            options={yearOptions}
            value={yearOptions.find((option) => option.value === String(resolved.year)) ?? null}
            onChange={(selected) => {
              const row = years.find((item) => String(item.year) === selected?.value);
              if (row) onChange(row);
            }}
            placeholder="Catalog year"
            styles={selectStyles}
            {...menu}
          />
        </Field>
      )}
    </>
  );
}
