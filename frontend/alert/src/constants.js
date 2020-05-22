export const DESKTOP = "1248px";
export const SMALLDESKTOP = "1100px";
export const TABLET = "900px";
export const PHONE = "584px";

export const minWidth = (w) => `@media screen and (min-width: ${w})`;
export const maxWidth = (w) => `@media screen and (max-width: ${w})`;
export const between = (l, h) =>
    `@media screen and (min-width: ${l}) and (max-width: ${h})`;
