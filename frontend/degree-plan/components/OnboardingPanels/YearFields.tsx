import Select from "react-select";
import {
  Field,
  FieldGrid,
  FieldLabel,
  Required,
  selectStyles,
} from "./onboardingStyles";
import { FieldError } from "./formLayout";

export type YearOption = { value: number; label: number };

export const yearOption = (year: number): YearOption => ({
  value: year,
  label: year,
});

type YearFieldsProps = {
  idPrefix: string;
  startOptions: YearOption[];
  graduationOptions: YearOption[];
  startingYear: YearOption | null;
  graduationYear: YearOption | null;
  setStartingYear: (year: YearOption | null) => void;
  setGraduationYear: (year: YearOption | null) => void;
  isClearable?: boolean;
};

export const yearsInOrder = (
  start: YearOption | null,
  graduation: YearOption | null
) => !!start && !!graduation && start.value < graduation.value;

export default function YearFields({
  idPrefix,
  startOptions,
  graduationOptions,
  startingYear,
  graduationYear,
  setStartingYear,
  setGraduationYear,
  isClearable = false,
}: YearFieldsProps) {
  const fields = [
    {
      id: `${idPrefix}-start-year`,
      label: "Starting year",
      term: "Fall",
      options: startOptions,
      value: startingYear,
      onChange: setStartingYear,
    },
    {
      id: `${idPrefix}-grad-year`,
      label: "Graduation year",
      term: "Spring",
      options: graduationOptions,
      value: graduationYear,
      onChange: setGraduationYear,
    },
  ];
  return (
    <>
      <FieldGrid $min={200}>
        {fields.map(({ id, label, term, options, value, onChange }) => (
          <Field key={id}>
            <FieldLabel htmlFor={id}>
              {label}
              <Required />
            </FieldLabel>
            <Select
              inputId={id}
              options={options}
              value={value}
              onChange={onChange}
              formatOptionLabel={(o) => `${term} ${o.value}`}
              getOptionValue={(o) => String(o.value)}
              isClearable={isClearable}
              placeholder="Select a year"
              styles={selectStyles}
              menuPortalTarget={
                typeof document !== "undefined" ? document.body : null
              }
            />
          </Field>
        ))}
      </FieldGrid>
      {startingYear &&
        graduationYear &&
        !yearsInOrder(startingYear, graduationYear) && (
          <FieldError role="alert">
            Graduation must come after your starting year.
          </FieldError>
        )}
    </>
  );
}
