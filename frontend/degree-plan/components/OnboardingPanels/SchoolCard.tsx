import { TrashIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import Select from "react-select";
import { DegreeListing, Major } from "@/types";
import {
  getAdditionalMajorOptions,
  getMajorOptions,
  SchoolSelection,
  takesAdditionalMajors,
} from "@/utils/parseUtils";
import {
  color,
  Field,
  FieldGrid,
  FieldLabel,
  Optional,
  Required,
  selectStyles,
} from "./onboardingStyles";

const Card = styled.div`
  border: 1px solid ${color.border};
  border-radius: 12px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px 14px 20px;
  border-bottom: 1px solid ${color.divider};
`;

const SchoolName = styled.span`
  font-size: 16px;
  font-weight: 600;
`;

const RemoveButton = styled.button`
  min-height: 36px;
  padding: 0 10px;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  color: ${color.muted};
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 6px;
  cursor: pointer;

  &:hover {
    background: #f4f5f7;
    color: ${color.text};
  }
`;

const CardBody = styled(FieldGrid)`
  padding: 20px;
`;

type SchoolCardProps = {
  selection: SchoolSelection;
  startingYear: number | null;
  degrees: DegreeListing[] | undefined;
  standaloneMajors: Major[] | undefined;
  isLoadingDegrees: boolean;
  isLoadingMajors: boolean;
  onChange: (changes: Partial<SchoolSelection>) => void;
  onRemove: () => void;
};

// A submatriculant starts their masters years after their undergraduate degree, so its majors
// come from the catalog of the year they started it rather than the plan's starting year.
const hasOwnStartYear = (school: SchoolSelection["school"]) => school.value === "MSE";

// One school the student is enrolled in, with its primary and additional majors.
export default function SchoolCard({
  selection: { school, primary, additional },
  startingYear,
  degrees,
  standaloneMajors,
  isLoadingDegrees,
  isLoadingMajors,
  onChange,
  onRemove,
}: SchoolCardProps) {
  const id = school.value.toLowerCase();
  // Wharton calls its majors concentrations.
  const majorWord = school.value === "BS" ? "concentration" : "major";

  const ownStartYear = hasOwnStartYear(school);
  // The catalog years this school has degrees for, most recent first.
  const startYearOptions = ownStartYear
    ? [...new Set((degrees ?? []).filter((d) => d.degree === school.value).map((d) => d.year))]
        .sort((a, b) => b - a)
        .map((year) => ({ value: year, label: year }))
    : [];

  return (
    <Card>
      <CardHeader>
        <SchoolName>{school.label}</SchoolName>
        <RemoveButton type="button" aria-label={`Remove ${school.label}`} onClick={onRemove}>
          <TrashIcon width={15} height={15} />
          Remove
        </RemoveButton>
      </CardHeader>
      <CardBody $min={240}>
        {ownStartYear && (
          <Field>
            <FieldLabel htmlFor={`${id}-start-year`}>
              Starting year
              <Required />
            </FieldLabel>
            <Select
              inputId={`${id}-start-year`}
              options={startYearOptions}
              value={startingYear ? { value: startingYear, label: startingYear } : null}
              // Majors are held to the year the program started, so changing it drops any that
              // belong to a different year.
              onChange={(selected) =>
                selected &&
                onChange({
                  startYear: selected.value,
                  primary: primary?.value.year === selected.value ? primary : null,
                  additional: additional.filter((m) => m.value.year === selected.value),
                })
              }
              formatOptionLabel={(o) => `Fall ${o.value}`}
              placeholder="Select a year"
              styles={selectStyles}
              menuPortalTarget={typeof document !== "undefined" ? document.body : null}
              isLoading={isLoadingDegrees}
            />
          </Field>
        )}
        <Field>
          <FieldLabel htmlFor={`${id}-primary`}>
            Primary {majorWord}
            <Required />
          </FieldLabel>
          <Select
            inputId={`${id}-primary`}
            options={getMajorOptions(degrees, school, startingYear)}
            value={primary}
            onChange={(selected) => onChange({ primary: selected })}
            isClearable
            isDisabled={!startingYear}
            placeholder={
              startingYear ? `Choose a ${majorWord}` : "Select your starting year first"
            }
            styles={selectStyles}
            menuPortalTarget={typeof document !== "undefined" ? document.body : null}
            isLoading={isLoadingDegrees}
          />
        </Field>
        {takesAdditionalMajors(school) && (
          <Field>
            <FieldLabel htmlFor={`${id}-additional`}>
              Additional {majorWord}s
              <Optional />
            </FieldLabel>
            <Select
              inputId={`${id}-additional`}
              options={getAdditionalMajorOptions(standaloneMajors, school, startingYear)}
              value={additional}
              onChange={(selected) => onChange({ additional: [...selected] })}
              isClearable
              isMulti
              isDisabled={!startingYear}
              placeholder="Add another"
              styles={selectStyles}
              menuPortalTarget={typeof document !== "undefined" ? document.body : null}
              isLoading={isLoadingMajors}
            />
          </Field>
        )}
      </CardBody>
    </Card>
  );
}
