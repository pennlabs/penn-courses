import styled from "@emotion/styled";
import React from "react";
import 'react-loading-skeleton/dist/skeleton.css'
import Skeleton from "react-loading-skeleton";
import { Icon } from "../common/bulma_derived_components";

export const PanelTopBarIcon = styled(Icon)`
    width: 1rem;
    height: 1rem;
    flex-shrink: 0;
`;

export const PanelTopBarString = styled.div`
    flex-shrink: 1;
`

export const PanelTopBarButton = styled.button`
    border: none;
    display: flex;
    flex-direction: row;
    justify-content: start;
    align-items: center;
    padding: .5rem 1rem;
    gap: .5rem;
    min-height: 1.5rem;
    font-family: inherit;

    font-size: 1rem;
    font-weight: 500;
    border-radius: 5px;
    color: var(--primary-color-xxx-dark);
`;
export const DarkBlueBackgroundSkeleton: React.FC<{ width?: string; }> = (props) => (
    <Skeleton
        baseColor="var(--primary-color-dark)"
        {...props} />
);

export const PanelHeader = styled.div`
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: var(--primary-color);
    color: var(--primary-color-ultra-dark);
    padding: 0.5rem 1rem;
    flex-grow: 0;
    font-weight: 300;
    align-items: center;
    min-height: 3rem;
`;

export const PanelBody = styled.div`
    padding: 1.5rem;
    height: 100%;
    overflow-y: auto;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: .5rem;
`;

export const PanelContainer = styled.div`
    border-radius: 10px;
    box-shadow: 0px 0px 10px 6px rgba(0, 0, 0, 0.05);
    background-color: #FFFFFF;
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    overflow: visible;
`;

export const PanelTopBarIconList = styled.div`
    display: flex;
    flex-direction: row;
    gap: 0.8rem;
`;

