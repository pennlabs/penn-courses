import { PlusIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import { Dispatch, SetStateAction, useMemo, useState } from "react";
import Select, { StylesConfig } from "react-select";
import { DegreeListing, Major, Minor } from "@/types";
import { SchoolSelection } from "@/utils/parseUtils";
import { schoolOptions } from "./SharedComponents";
import { color, selectStyles } from "./onboardingStyles";
import SchoolCard from "./SchoolCard";

const SchoolList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

// Groups the add button and the school cards; matches the imported-courses box.
const SchoolsBox = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: #f8f9fb;
  border: 1px solid ${color.border};
  border-radius: 12px;
`;

const AddSchoolButton = styled.button`
  min-height: 52px;
  border: 1.5px dashed var(--primary-color-extra-dark);
  border-radius: 12px;
  background: #ffffff;
  font: inherit;
  font-size: 15px;
  font-weight: 500;
  color: ${color.accent};
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;

  &:hover {
    border-color: ${color.accent};
    background: var(--primary-color-light);
  }
`;

// The school picker replaces AddSchoolButton in place, so it takes the button's size and corners.
const addSchoolSelectStyles: StylesConfig<any, boolean> = {
  ...selectStyles,
  control: (provided, state) => ({
    ...selectStyles.control!(provided, state),
    minHeight: 52,
    borderRadius: 12,
  }),
};

type SchoolsFieldProps = {
  selections: SchoolSelection[];
  setSelections: Dispatch<SetStateAction<SchoolSelection[]>>;
  degrees: DegreeListing[] | undefined;
  standaloneMajors: Major[] | undefined;
  minors: Minor[] | undefined;
  isLoadingDegrees: boolean;
  isLoadingMajors: boolean;
  isLoadingMinors: boolean;
};

export default function SchoolsField({
  selections,
  setSelections,
  degrees,
  standaloneMajors,
  minors,
  isLoadingDegrees,
  isLoadingMajors,
  isLoadingMinors,
}: SchoolsFieldProps) {
  const [addingSchool, setAddingSchool] = useState(false);

  const addableSchools = useMemo(
    () =>
      schoolOptions.filter(
        (o) => !selections.some((s) => s.school.value === o.value)
      ),
    [selections]
  );

  return (
    <SchoolsBox>
      {addableSchools.length > 0 &&
        (addingSchool ? (
          <Select
            aria-label="Add a school or program"
            options={addableSchools}
            value={null}
            onChange={(selected) => {
              if (selected)
                setSelections((current) => [
                  { school: selected, primary: null, additional: [] },
                  ...current,
                ]);
              setAddingSchool(false);
            }}
            onMenuClose={() => setAddingSchool(false)}
            autoFocus
            defaultMenuIsOpen
            placeholder="Choose a school or program"
            styles={addSchoolSelectStyles}
            menuPortalTarget={
              typeof document !== "undefined" ? document.body : null
            }
            isLoading={isLoadingDegrees}
          />
        ) : (
          <AddSchoolButton type="button" onClick={() => setAddingSchool(true)}>
            <PlusIcon width={16} height={16} />
            Add a school or program
          </AddSchoolButton>
        ))}

      {selections.length > 0 && (
        <SchoolList role="region" aria-label="Your schools">
          {selections.map((selection) => (
            <SchoolCard
              key={selection.key ?? selection.school.value}
              selection={selection}
              degrees={degrees}
              standaloneMajors={standaloneMajors}
              minors={minors}
              isLoadingDegrees={isLoadingDegrees}
              isLoadingMajors={isLoadingMajors}
              isLoadingMinors={isLoadingMinors}
              onChange={(changes) =>
                setSelections((current) =>
                  current.map((s) =>
                    s === selection ? { ...s, ...changes } : s
                  )
                )
              }
              onRemove={() =>
                setSelections((current) =>
                  current.filter((s) => s !== selection)
                )
              }
            />
          ))}
        </SchoolList>
      )}
    </SchoolsBox>
  );
}
