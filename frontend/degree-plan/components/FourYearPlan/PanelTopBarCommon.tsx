import { Icon } from "../common/bulma_derived_components";
import styled from "@emotion/styled";

export const PanelTopBarIcon = styled(Icon)`
    width: 1rem;
    height: 1rem;
    color: #FFFFFF;
    flex-shrink: 0;
`;

export const PanelTopBarString = styled.div`
    flex-shrink: 1;
`

export const PanelTopBarButton = styled.div`
    display: flex;
    flex-direction: row;
    justify-content: start;
    align-items: center;
    padding: 0 1rem;
    gap: .5rem;
    min-height: 1.5rem;

    font-size: 1rem !important;
    font-weight: 500;
   
    background: var(--primary-color-xx-dark); 
    border-radius: 5px;
    color: #FFFFFF;
`;

