import styled from "@emotion/styled";
import { GrayIcon } from "./bulma_derived_components";

export const TrashIcon = styled(GrayIcon)`
    pointer-events: auto;
    color: #b2b2b2;
    &:hover {
        color: #7e7e7e;
    }
`;

export const LightTrashIcon = styled(GrayIcon)`
    pointer-events: auto;
    color: #f5f5f5;
    &:hover {
        color: #e0e0e0;
    }
`;
