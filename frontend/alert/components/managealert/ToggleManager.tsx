import React from "react";
import styled from "styled-components";
import { Flex, FlexProps } from "pcx-shared-components/src/common/layout";
import { Img, P } from "../common/common";
import { AlertAction, WrappedStyled } from "../../types";
import ToggleSwitch from "../common/ToggleSwitch";

type ActionFlexProps = FlexProps & {
    background: string;
};

// Component associated with Resubscribe and Cancel buttons
// for each alert
interface ToggleManagerProps {
    type: AlertAction;
    handleChange: () => void;
}
export const ToggleManager = ({ type, handleChange }: ToggleManagerProps) => {
    let checked;

    switch (type) {
        case AlertAction.ONALERT:
            checked = false;
            break;
        case AlertAction.OFFALERT:
            checked = true;
            break;
        case AlertAction.ONCLOSED:
            checked = false;
            break;
        case AlertAction.OFFCLOSED:
            checked = true;
            break;
        case AlertAction.NOEFFECT:
            checked = false;
            break;
        default:
    }

    return <ToggleSwitch handleChange={handleChange} isChecked={checked} />;
};
