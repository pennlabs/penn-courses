import React from "react";
import styled from '@emotion/styled';
import { PanelTopBarButton, PanelTopBarIcon, PanelTopBarString } from "./PanelCommon";

const EditButtonWrapper = styled(PanelTopBarButton)`
    min-width: 5.5rem; /* Specify width so size does not change */
`

export const EditButton = ({ editMode, setEditMode }: { editMode: boolean; setEditMode: (arg0: boolean) => void; }) => (
    <EditButtonWrapper onClick={() => setEditMode(!editMode)}>
        <PanelTopBarIcon>
            {editMode ? 
            <i className="fas fa-md fa-check"/> :
            <i className="fas fa-md fa-edit" />
            }
        </PanelTopBarIcon>
        <PanelTopBarString>
            {editMode ? "Done" : "Edit" }
        </PanelTopBarString>
    </EditButtonWrapper>
);
