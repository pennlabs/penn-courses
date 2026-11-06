import { TrashIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import Select from "react-select";
import { DegreeListing, Major, Minor } from "@/types";
import {
  getAdditionalMajorOptions,
  getMajorOptions,
  getMinorOptions,
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

type SchoolCardProps = {
  selection: SchoolSelection;
  degrees: DegreeListing[] | undefined;
  standaloneMajors: Major[] | undefined;
  minors: Minor[] | undefined;
  isLoadingDegrees: boolean;
  isLoadingMajors: boolean;
  isLoadingMinors: boolean;
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
  onChange,
  onRemove,
}: SchoolCardProps) {
  const id = school.value.toLowerCase();
  // Wharton calls its majors concentrations.
  const majorWord = school.value === "BS" ? "concentration" : "major";

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
        <Field>
          <FieldLabel htmlFor={`${id}-primary`}>
            Primary {majorWord}
            <Required />
          </FieldLabel>
          <Select
            inputId={`${id}-primary`}
            options={getMajorOptions(degrees, school)}
            value={primary}
            onChange={(selected) => onChange({ primary: selected })}
            isClearable
            placeholder={`Choose a ${majorWord}`}
            getOptionValue={optionId}
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
              options={getAdditionalMajorOptions(standaloneMajors, school)}
              value={additional}
              onChange={(selected) => onChange({ additional: [...selected] })}
              isClearable
              isMulti
              placeholder="Add another"
              getOptionValue={optionId}
              styles={selectStyles}
              menuPortalTarget={typeof document !== "undefined" ? document.body : null}
              isLoading={isLoadingMajors}
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
