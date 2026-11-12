import styled from "@emotion/styled";
import { StylesConfig } from "react-select";
import { inter } from "@/fonts";

export const color = {
  text: "var(--text-color)",
  heading: "var(--primary-color-ultra-dark)",
  muted: "#777777",
  subtle: "#6B7280",
  border: "#E2E5EB",
  inputBorder: "#D5D9E0",
  divider: "#EEF0F3",
  accent: "var(--primary-color-xxx-dark)",
  accentHover: "var(--primary-color-ultra-dark)",
  focusRing: "0 0 0 3px rgba(108, 114, 182, 0.2)",
  required: "var(--error-color)",
};

export const Field = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
`;

export const FieldGrid = styled.div<{ $min: number }>`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(${({ $min }) => $min}px, 100%), 1fr));
  gap: 16px;
`;

export const FieldLabel = styled.label`
  font-size: 14px;
  font-weight: 600;
  color: ${color.heading};
`;

export const Required = () => <span style={{ color: color.required }}> *</span>;

export const Optional = () => (
  <span style={{ fontWeight: 400, color: color.subtle }}> (optional)</span>
);

export const selectStyles: StylesConfig<any, boolean> = {
  control: (provided, state) => ({
    ...provided,
    minHeight: 44,
    borderRadius: 8,
    borderColor: state.isFocused ? color.accent : color.inputBorder,
    boxShadow: state.isFocused ? color.focusRing : "none",
    backgroundColor: state.isDisabled ? "#F8F9FB" : "#FFFFFF",
    fontSize: 15,
    "&:hover": { borderColor: state.isFocused ? color.accent : "var(--primary-color-extra-dark)" },
  }),
  valueContainer: (provided) => ({ ...provided, padding: "2px 12px" }),
  placeholder: (provided) => ({ ...provided, color: color.subtle }),
  singleValue: (provided) => ({ ...provided, color: color.text }),
  indicatorSeparator: () => ({ display: "none" }),
  dropdownIndicator: (provided) => ({ ...provided, color: color.subtle }),
  menu: (provided) => ({
    ...provided,
    borderRadius: 8,
    boxShadow: "0 8px 24px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(61, 65, 119, 0.06)",
  }),
  menuList: (provided) => ({ ...provided, padding: 6 }),
  // Menus are portaled to <body> so they aren't clipped by the scrollable school list.
  menuPortal: (provided) => ({
    ...provided,
    zIndex: 9100,
    fontFamily: inter.style.fontFamily,
  }),
  option: (provided, state) => ({
    ...provided,
    borderRadius: 6,
    fontSize: 14,
    fontWeight: state.isSelected ? 700 : 500,
    color: color.heading,
    backgroundColor:
      state.isSelected || state.isFocused ? "var(--primary-color-light)" : "#FFFFFF",
    "&:active": { backgroundColor: "var(--primary-color)" },
  }),
  multiValue: (provided) => ({
    ...provided,
    borderRadius: 6,
    backgroundColor: "var(--primary-color-light)",
    maxWidth: 220,
  }),
  multiValueLabel: (provided) => ({
    ...provided,
    color: color.heading,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  loadingIndicator: (provided) => ({ ...provided, color: color.subtle }),
};
