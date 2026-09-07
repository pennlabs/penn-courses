/*
  Every value here is a reference to a custom property declared in tokens.css
  This file just gives them names that styled-components and TypeScript understand
*/
export const theme = {
  color: {
    text: {
      primary: "var(--pcr-color-text-primary)",
      secondary: "var(--pcr-color-text-secondary)",
      muted: "var(--pcr-color-text-muted)",
      subtle: "var(--pcr-color-text-subtle)",
      faint: "var(--pcr-color-text-faint)",
      dim: "var(--pcr-color-text-dim)",
      strong: "var(--pcr-color-text-strong)",
      heading: "var(--pcr-color-text-heading)",
      legacy: "var(--pcr-color-text-legacy)",
      inverse: "var(--pcr-color-text-inverse)",
      black: "var(--pcr-color-text-black)",
      link: "var(--pcr-color-text-link)",
      linkHover: "var(--pcr-color-text-link-hover)",
    },
    surface: {
      page: "var(--pcr-color-surface-page)",
      card: "var(--pcr-color-surface-card)",
      subtle: "var(--pcr-color-surface-subtle)",
      muted: "var(--pcr-color-surface-muted)",
      hover: "var(--pcr-color-surface-hover)",
      selected: "var(--pcr-color-surface-selected)",
      selectedHover: "var(--pcr-color-surface-selected-hover)",
      disabled: "var(--pcr-color-surface-disabled)",
    },
    border: {
      default: "var(--pcr-color-border-default)",
      strong: "var(--pcr-color-border-strong)",
      divider: "var(--pcr-color-border-divider)",
      muted: "var(--pcr-color-border-muted)",
      input: "var(--pcr-color-border-input)",
      focus: "var(--pcr-color-border-focus)",
      selected: "var(--pcr-color-border-selected)",
    },
    accent: {
      default: "var(--pcr-color-accent-default)",
      hover: "var(--pcr-color-accent-hover)",
      subtle: "var(--pcr-color-accent-subtle)",
      subtleBorder: "var(--pcr-color-accent-subtle-border)",
    },
    feedback: {
      errorFg: "var(--pcr-color-feedback-error-fg)",
      errorBg: "var(--pcr-color-feedback-error-bg)",
      errorBorder: "var(--pcr-color-feedback-error-border)",
      errorAccent: "var(--pcr-color-feedback-error-accent)",
    },
  },

  font: {
    family: {
      sans: "var(--pcr-font-family-sans)",
    },
    size: {
      xs: "var(--pcr-font-size-xs)",
      sm: "var(--pcr-font-size-sm)",
      md: "var(--pcr-font-size-md)",
      lg: "var(--pcr-font-size-lg)",
      xl: "var(--pcr-font-size-xl)",
      "2xl": "var(--pcr-font-size-2xl)",
      "3xl": "var(--pcr-font-size-3xl)",
      "4xl": "var(--pcr-font-size-4xl)",
    },
    weight: {
      light: "var(--pcr-font-weight-light)",
      regular: "var(--pcr-font-weight-regular)",
      medium: "var(--pcr-font-weight-medium)",
      semibold: "var(--pcr-font-weight-semibold)",
      bold: "var(--pcr-font-weight-bold)",
    },
  },

  radius: {
    sm: "var(--pcr-radius-sm)",
    md: "var(--pcr-radius-md)",
    lg: "var(--pcr-radius-lg)",
    pill: "var(--pcr-radius-pill)",
    circle: "var(--pcr-radius-circle)",
  },

  shadow: {
    dropdown: "var(--pcr-shadow-dropdown)",
    card: "var(--pcr-shadow-card)",
  },

  zIndex: {
    dropdown: "var(--pcr-z-index-dropdown)",
    header: "var(--pcr-z-index-header)",
  },

  size: {
    sidebarWidth: "var(--pcr-size-sidebar-width)",
    filterWidgetMax: "var(--pcr-size-filter-widget-max)",
    controlHeight: "var(--pcr-size-control-height)",
  },
};

export type Theme = typeof theme;

export default theme;
