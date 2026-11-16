import React from "react";
import styled from '@emotion/styled';
import { PanelTopBarButton, PanelTopBarIcon, PanelTopBarString } from "./PanelCommon";

const EditButtonWrapper = styled(PanelTopBarButton)<{ $wide?: boolean }>`
    min-width: ${(props) => (props.$wide ? "9rem" : "5.5rem")}; /* Specify width so size does not change */
`

export const EditButton = ({
    editMode,
    setEditMode,
    label = "Edit",
}: {
    editMode: boolean;
    setEditMode: (arg0: boolean) => void;
    label?: string;
}) => (
    <EditButtonWrapper $wide={label !== "Edit"} onClick={() => setEditMode(!editMode)}>
        <PanelTopBarIcon>
            {editMode ? 
            <i className="fas fa-md fa-check"/> :
            <i className="fas fa-md fa-edit" />
            }
        </PanelTopBarIcon>
        <PanelTopBarString>
            {editMode ? "Done" : label }
        </PanelTopBarString>
    </EditButtonWrapper>
);
