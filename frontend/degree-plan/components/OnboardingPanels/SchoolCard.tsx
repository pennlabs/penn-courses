import { Cross2Icon, TrashIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import Select from "react-select";
import { DegreeListing, Major, Minor } from "@/types";
import { CatalogRow } from "@/utils/degreeChoice";
import {
  degreeCodeOf,
  getMinorOptions,
  majorOption,
  SchoolSelection,
  takesAdditionalMajors,
} from "@/utils/parseUtils";
import {
  color,
  Field,
  FieldGrid,
  FieldLabel,
  Optional,
  selectStyles,
} from "./onboardingStyles";
import DegreeSteps from "./DegreeSteps";

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
  font-weight: 700;
  color: ${color.heading};
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
    background: rgba(61, 65, 119, 0.08);
    color: var(--error-color);
  }
`;

const CardBody = styled(FieldGrid)`
  padding: 20px;
`;

// Options are compared by id, so a value read from a saved plan matches its option.
const optionId = <T extends { value: { id: number } }>(option: T) => String(option.value.id);

const Chosen = styled.ul`
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
`;

const ChosenRow = styled.li`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 14px;
`;

const RemoveChoice = styled.button`
  border: 0;
  background: transparent;
  color: ${color.muted};
  cursor: pointer;
  display: flex;
  padding: 4px;
`;

type SchoolCardProps = {
  selection: SchoolSelection;
  degrees: DegreeListing[] | undefined;
  standaloneMajors: Major[] | undefined;
  minors: Minor[] | undefined;
  isLoadingDegrees: boolean;
  isLoadingMajors: boolean;
  isLoadingMinors: boolean;
  startYear: number | null;
  onChange: (changes: Partial<SchoolSelection>) => void;
  onRemove: () => void;
};

// One school the student is enrolled in, with its primary and additional majors and its minors.
export default function SchoolCard({
  selection: { school, primary, additional, minors: chosenMinors = [] },
  degrees,
  standaloneMajors,
  minors,
  isLoadingDegrees,
  isLoadingMajors,
  isLoadingMinors,
  startYear,
  onChange,
  onRemove,
}: SchoolCardProps) {
  const id = school.value.toLowerCase();
  const degreeRows = (degrees ?? []).filter((degree) => degree.degree === school.value);
  const majorRows = (standaloneMajors ?? [])
    .filter((major) => degreeCodeOf(major.program_code) !== "MSE")
    .map((major) => {
      const own = degreeCodeOf(major.program_code) === school.value;
      return {
        ...major,
        major: major.code,
        major_name: own
          ? major.name || major.code
          : `${major.name || major.code}, ${degreeCodeOf(major.program_code)}`,
        choiceKey: major.program_code,
      };
    });

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
        <DegreeSteps
          id={`${id}-primary`}
          rows={degreeRows}
          value={primary?.value ?? null}
          startYear={startYear}
          isLoading={isLoadingDegrees}
          required
          onChange={(row) =>
            onChange({
              primary: row
                ? {
                    value: row as DegreeListing,
                    label: `${row.major_name || row.major} (${row.year})`,
                  }
                : null,
            })
          }
        />
        {takesAdditionalMajors(school) && (
          <Field>
            <FieldLabel>
              Additional majors
              <Optional />
            </FieldLabel>
            {additional.length > 0 && (
              <Chosen>
                {additional.map((major) => (
                  <ChosenRow key={major.value.id}>
                    <span>{major.label}</span>
                    <RemoveChoice
                      type="button"
                      aria-label={`Remove ${major.label}`}
                      onClick={() =>
                        onChange({
                          additional: additional.filter((item) => item.value.id !== major.value.id),
                        })
                      }
                    >
                      <Cross2Icon />
                    </RemoveChoice>
                  </ChosenRow>
                ))}
              </Chosen>
            )}
            <DegreeSteps
              key={additional.map((major) => major.value.id).join("-") || "none"}
              id={`${id}-additional`}
              rows={majorRows.filter(
                (major) => !additional.some((item) => item.value.id === major.id)
              )}
              value={null}
              startYear={startYear}
              isLoading={isLoadingMajors}
              onChange={(row) => {
                const major = row && majorRows.find((item) => item.id === row.id);
                if (!major) return;
                onChange({
                  additional: [...additional, majorOption(major, school)],
                });
              }}
            />
          </Field>
        )}
        {takesAdditionalMajors(school) && (
          <Field>
            <FieldLabel htmlFor={`${id}-minors`}>
              Minors
              <Optional />
            </FieldLabel>
            <Select
              inputId={`${id}-minors`}
              options={getMinorOptions(minors)}
              value={chosenMinors}
              onChange={(selected) => onChange({ minors: [...selected] })}
              isClearable
              isMulti
              placeholder="Add a minor"
              getOptionValue={optionId}
              styles={selectStyles}
              menuPortalTarget={typeof document !== "undefined" ? document.body : null}
              isLoading={isLoadingMinors}
            />
          </Field>
        )}
      </CardBody>
    </Card>
  );
}
