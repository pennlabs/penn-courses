import styled from "@emotion/styled";
import { StylesConfig } from "react-select";
import { inter } from "@/fonts";

export const color = {
  text: "var(--foreground-rgb)",
  muted: "#777777",
  subtle: "#6B7280",
  border: "#E2E5EB",
  inputBorder: "#D5D9E0",
  divider: "#EEF0F3",
  accent: "#2F4FD8",
  accentHover: "#1E3AB0",
  required: "#B42318",
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
    boxShadow: state.isFocused ? "0 0 0 3px rgba(47, 79, 216, 0.15)" : "none",
    backgroundColor: state.isDisabled ? "#F8F9FB" : "#FFFFFF",
    fontSize: 15,
    "&:hover": { borderColor: state.isFocused ? color.accent : "#C4C9D2" },
  }),
  valueContainer: (provided) => ({ ...provided, padding: "2px 12px" }),
  placeholder: (provided) => ({ ...provided, color: color.subtle }),
  singleValue: (provided) => ({ ...provided, color: color.text }),
  indicatorSeparator: () => ({ display: "none" }),
  dropdownIndicator: (provided) => ({ ...provided, color: color.subtle }),
  menu: (provided) => ({ ...provided, borderRadius: 8 }),
  // Menus are portaled to <body> so they aren't clipped by the scrollable school list.
  menuPortal: (provided) => ({
    ...provided,
    zIndex: 1000,
    fontFamily: inter.style.fontFamily,
  }),
  option: (provided, state) => ({
    ...provided,
    fontSize: 14,
    color: color.text,
    backgroundColor: state.isSelected
      ? "#E8ECFB"
      : state.isFocused
      ? "#F4F5F7"
      : "#FFFFFF",
  }),
  multiValue: (provided) => ({
    ...provided,
    borderRadius: 6,
    backgroundColor: "#EEF1FD",
    maxWidth: 220,
  }),
  multiValueLabel: (provided) => ({
    ...provided,
    color: color.text,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  loadingIndicator: (provided) => ({ ...provided, color: color.subtle }),
};
